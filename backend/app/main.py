
import logging
import pickle
import os
import io # 이미지 바이트 처리를 위해 추가
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime # 로그 저장을 위해 추가

import pymysql
import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from dotenv import load_dotenv

# (추가) CORS 미들웨어
from fastapi.middleware.cors import CORSMiddleware
# (추가) 정적 파일 서빙
from fastapi.staticfiles import StaticFiles

# AI/ML 라이브러리
import torch
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from PIL import Image # 이미지 처리 라이브러리 (Pillow)
# --- 0. 로깅 및 경로 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 경로 설정
APP_DIR = Path(__file__).parent # backend/app/
BACKEND_ROOT = APP_DIR.parent # backend/
PROJECT_ROOT = BACKEND_ROOT.parent # LMM-Product-Search/
DATA_DIR = PROJECT_ROOT / "data"

# .env 파일 로드 (backend/.env)
load_dotenv(BACKEND_ROOT / ".env")

# --- 1. 전역 변수 및 모델 로드 설정 ---

# 이 딕셔너리에 AI 모델과 데이터를 저장합니다.
ml_models = {}

# DB 접속 정보
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "lmm_project")

MODEL_ID = "openai/clip-vit-base-patch32"
VECTOR_DB_PATH = DATA_DIR / "product_vectors.pkl"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 서버 시작 (Startup) ---
    logger.info("서버 시작... AI 모델 및 벡터 DB를 로드합니다.")
    
    # 1. CLIP 모델 로드
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"사용 디바이스: {device}")
        
        model = CLIPModel.from_pretrained(MODEL_ID, use_safetensors=True).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_ID, use_safetensors=True)
        
        ml_models["clip_model"] = model
        ml_models["clip_processor"] = processor
        ml_models["device"] = device
        
        logger.info("✅ CLIP 모델 로드 성공!")
    except Exception as e:
        logger.error(f"❌ CLIP 모델 로드 실패: {e}")

    # 2. 벡터 DB (.pkl) 로드
    try:
        with open(VECTOR_DB_PATH, 'rb') as f:
            vector_data = pickle.load(f)
            ml_models["db_ids"] = [item['id'] for item in vector_data]
            ml_models["db_vectors"] = np.array([item['vector'] for item in vector_data])
            logger.info(f"✅ 벡터 DB 로드 성공! ({len(ml_models['db_ids'])}개)")
    except FileNotFoundError:
        logger.error(f"❌ 벡터 DB 파일({VECTOR_DB_PATH})을 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"❌ 벡터 DB 로드 실패: {e}")

    yield # --- 여기가 API가 실행되는 시점 ---

    # --- 서버 종료 (Shutdown) ---
    logger.info("서버 종료... 리소스를 정리합니다.")
    ml_models.clear()


# --- 2. FastAPI 앱 생성 및 설정 ---

app = FastAPI(lifespan=lifespan)

# (추가) CORS 미들웨어 설정
origins = [
    "http://localhost",
    "http://localhost:5173", # React 개발 서버 주소
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# (추가) 정적 파일(이미지) 서빙 설정
static_images_path = PROJECT_ROOT / "data" / "images"
app.mount("/static/images", StaticFiles(directory=static_images_path), name="static_images")


# --- 3. DB 연결 및 헬퍼 함수 ---

def get_db_connection():
    """MySQL DB 연결을 생성합니다."""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"❌ DB 연결 실패: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 연결에 실패했습니다.")


def save_search_log(search_type: str, query: str = None, filename: str = None):
    """(관리자 기능) 사용자 검색 기록을 DB에 저장합니다."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO search_logs (search_type, query, filename)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (search_type, query, filename))
        conn.commit()
        conn.close()
        logger.info(f"📝 검색 로그 저장 완료: type={search_type}, query={query or filename}")
    except Exception as e:
        logger.error(f"❌ 로그 저장 실패: {e}") # 로그 저장이 실패해도 검색은 되어야 함


# --- 4. Pydantic 모델 정의 ---

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class ProductResponse(BaseModel):
    id: str
    product_name: str | None = None
    description: str | None = None
    image_file: str | None = None


# --- 5. API 엔드포인트 구현 ---

@app.get("/")
def read_root():
    return {"message": "LMM 제품 검색 API (Modify)"}


@app.post("/search/text", response_model=list[ProductResponse])
async def search_by_text(request: SearchRequest):
    """텍스트 쿼리를 받아 AI 벡터 검색 후 DB에서 제품 정보를 반환합니다."""
    
    # 1. 로그 저장
    save_search_log(search_type="text", query=request.query)
    
    logger.info(f"텍스트 검색 요청 받음: query='{request.query}', top_k={request.top_k}")

    # 2. AI 모델/데이터 준비
    if "clip_model" not in ml_models or "db_vectors" not in ml_models:
        raise HTTPException(status_code=500, detail="AI 모델이 준비되지 않았습니다.")
        
    model = ml_models["clip_model"]
    processor = ml_models["clip_processor"]
    device = ml_models["device"]
    db_ids = ml_models["db_ids"]
    db_vectors = ml_models["db_vectors"]

    # 3. (AI) 텍스트 쿼리 -> 벡터로 변환
    try:
        inputs = processor(text=[request.query], return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            query_vector = model.get_text_features(**inputs)
        query_vector_np = query_vector.squeeze().cpu().numpy().reshape(1, -1)
    except Exception as e:
        logger.error(f"❌ 쿼리 벡터 변환 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="검색어 처리 중 오류 발생")

    # 4. (AI) 코사인 유사도 계산
    similarities = cosine_similarity(query_vector_np, db_vectors)
    top_k_indices = np.argsort(similarities[0])[-request.top_k:][::-1]
    top_k_ids = [db_ids[i] for i in top_k_indices]
    logger.info(f"AI 검색 결과 (Top {request.top_k} ID): {top_k_ids}")

    # 5. (DB) MySQL에서 제품 상세 정보 조회
    if not top_k_ids:
        return []

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            id_tuple = tuple(top_k_ids)
            field_placeholders = ', '.join(['%s'] * len(top_k_ids))
            sql = f"""
                SELECT id, product_name, description, image_file 
                FROM products 
                WHERE id IN %s
                ORDER BY FIELD(id, {field_placeholders})
            """
            params = (id_tuple,) + tuple(top_k_ids)
            cursor.execute(sql, params)
            results = cursor.fetchall() 
            logger.info(f"DB 조회 결과: {len(results)}개 반환")
            return results
    except pymysql.MySQLError as e:
        logger.error(f"❌ DB 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="제품 정보 조회 중 오류 발생")
    finally:
        conn.close()


@app.post("/search/image", response_model=list[ProductResponse])
async def search_by_image(file: UploadFile = File(...), top_k: int = 5):
    """업로드된 이미지를 받아 AI 벡터 검색 후 DB에서 제품 정보를 반환합니다."""
    
    # 1. 로그 저장
    save_search_log(search_type="image", filename=file.filename)

    logger.info(f"이미지 검색 요청 받음: filename='{file.filename}', top_k={top_k}")

    # 2. AI 모델/데이터 준비
    if "clip_model" not in ml_models or "db_vectors" not in ml_models:
        raise HTTPException(status_code=500, detail="AI 모델이 준비되지 않았습니다.")
    model, processor, device, db_ids, db_vectors = (
        ml_models["clip_model"], ml_models["clip_processor"], ml_models["device"],
        ml_models["db_ids"], ml_models["db_vectors"]
    )

    # 3. (AI) 이미지 쿼리 -> 벡터로 변환
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        inputs = processor(images=image, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            query_vector = model.get_image_features(**inputs)
        query_vector_np = query_vector.squeeze().cpu().numpy().reshape(1, -1)
    except Exception as e:
        logger.error(f"❌ 쿼리 이미지 벡터 변환 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="이미지 처리 중 오류 발생")

    # 4. (AI) 코사인 유사도 계산 (텍스트 검색과 동일)
    similarities = cosine_similarity(query_vector_np, db_vectors)
    top_k_indices = np.argsort(similarities[0])[-top_k:][::-1]
    top_k_ids = [db_ids[i] for i in top_k_indices]
    logger.info(f"AI 검색 결과 (Top {top_k} ID): {top_k_ids}")

    # 5. (DB) MySQL에서 제품 상세 정보 조회 (텍스트 검색과 동일)
    if not top_k_ids:
        return []

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            id_tuple = tuple(top_k_ids)
            field_placeholders = ', '.join(['%s'] * len(top_k_ids))
            sql = f"""
                SELECT id, product_name, description, image_file 
                FROM products 
                WHERE id IN %s
                ORDER BY FIELD(id, {field_placeholders})
            """
            params = (id_tuple,) + tuple(top_k_ids)
            cursor.execute(sql, params)
            results = cursor.fetchall()
            logger.info(f"DB 조회 결과: {len(results)}개 반환")
            return results
    except pymysql.MySQLError as e:
        logger.error(f"❌ DB 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="제품 정보 조회 중 오류 발생")
    finally:
        conn.close()


@app.get("/search/related/{item_id}", response_model=list[ProductResponse])
async def search_by_related_item(item_id: str, top_k: int = 5):
    """(아이디어 1) 특정 item_id와 유사한 AI 벡터 검색 결과를 반환합니다."""
    
    # 1. 로그 저장 (연관 검색도 로그로 남김)
    save_search_log(search_type="related", query=item_id)
    
    logger.info(f"연관 상품 검색 요청 받음: item_id='{item_id}', top_k={top_k}")

    # 2. AI 모델/데이터 준비
    if "db_ids" not in ml_models or "db_vectors" not in ml_models:
        raise HTTPException(status_code=500, detail="AI 모델이 준비되지 않았습니다.")
    db_ids = ml_models["db_ids"]
    db_vectors = ml_models["db_vectors"]

    # 3. (AI) item_id로 쿼리 벡터 찾기
    try:
        query_index = db_ids.index(item_id)
        query_vector_np = db_vectors[query_index].reshape(1, -1)
    except ValueError:
        raise HTTPException(status_code=404, detail="아이템 ID를 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"❌ 쿼리 벡터 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="아이템 처리 중 오류 발생")

    # 4. (AI) 코사인 유사도 계산
    similarities = cosine_similarity(query_vector_np, db_vectors)
    total_to_find = top_k + 1 # 자기 자신 포함
    top_k_indices = np.argsort(similarities[0])[-total_to_find:][::-1]
    
    top_k_ids = []
    for i in top_k_indices:
        if db_ids[i] != item_id: # 자기 자신 제외
            top_k_ids.append(db_ids[i])
        if len(top_k_ids) == top_k:
            break
            
    logger.info(f"AI 연관 검색 결과 (Top {top_k} ID): {top_k_ids}")

    # 5. (DB) MySQL에서 제품 상세 정보 조회 (재활용)
    if not top_k_ids:
        return []

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            id_tuple = tuple(top_k_ids)
            field_placeholders = ', '.join(['%s'] * len(top_k_ids))
            sql = f"""
                SELECT id, product_name, description, image_file 
                FROM products 
                WHERE id IN %s
                ORDER BY FIELD(id, {field_placeholders})
            """
            params = (id_tuple,) + tuple(top_k_ids)
            cursor.execute(sql, params)
            results = cursor.fetchall()
            logger.info(f"DB 조회 결과: {len(results)}개 반환")
            return results
    except pymysql.MySQLError as e:
        logger.error(f"❌ DB 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="제품 정보 조회 중 오류 발생")
    finally:
        conn.close()


@app.get("/admin/logs")
def get_search_logs():
    """(관리자 기능) 저장된 모든 검색 로그를 최신순으로 반환합니다."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # (보안 참고: 실제 프로덕션에선 페이지네이션(LIMIT/OFFSET)을 구현해야 합니다)
            sql = "SELECT * FROM search_logs ORDER BY created_at DESC LIMIT 100"
            cursor.execute(sql)
            logs = cursor.fetchall()
        conn.close()
        return logs
    except Exception as e:
        logger.error(f"❌ 로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="로그 조회 실패")

@app.get("/product/{item_id}", response_model=ProductResponse)
async def get_product_details(item_id: str):
    """
    특정 item_id의 상세 제품 정보 1개를 DB에서 조회합니다.
    """
    logger.info(f"상품 상세 정보 요청 받음: item_id='{item_id}'")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, product_name, description, image_file FROM products WHERE id = %s"
            cursor.execute(sql, (item_id,))
            product = cursor.fetchone() # 1개의 결과만 가져옴
            
            if product:
                return product
            else:
                logger.error(f"❌ DB에서 item_id '{item_id}'를 찾을 수 없습니다.")
                raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    except pymysql.MySQLError as e:
        logger.error(f"❌ DB 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="제품 정보 조회 중 오류 발생")
    finally:
        conn.close()


# --- 6. 서버 실행 (로컬 테스트용) ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)