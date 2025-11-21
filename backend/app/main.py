import logging
import pickle
import os
import io
import json
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

import pymysql
import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from dotenv import load_dotenv

# FastAPI 미들웨어
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# AI/ML 라이브러리
import torch
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from PIL import Image 

# 번역기 (일반 검색용)
from deep_translator import GoogleTranslator

# IBM Watsonx 라이브러리 (스마트 검색용)
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# --- 0. 설정 ---
# 로그 레벨 설정 (INFO)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 경로 설정
APP_DIR = Path(__file__).parent 
BACKEND_ROOT = APP_DIR.parent 
PROJECT_ROOT = BACKEND_ROOT.parent 
DATA_DIR = PROJECT_ROOT / "data"

# .env 파일 로드
load_dotenv(BACKEND_ROOT / ".env")

# 전역 변수 (모델 저장용)
ml_models = {}

# DB 정보
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "lmm_project")

# IBM Watson 정보
WATSONX_API_KEY = os.environ.get("WATSONX_API_KEY")
WATSONX_PROJECT_ID = os.environ.get("WATSONX_PROJECT_ID")
WATSONX_URL = os.environ.get("WATSONX_URL")

# 모델 ID 및 벡터 DB 경로
MODEL_ID = "openai/clip-vit-base-patch32"
VECTOR_DB_PATH = DATA_DIR / "product_vectors.pkl"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 로직 (모델 로드)"""
    logger.info("서버 시작... AI 모델 및 벡터 로드")
    
    # 1. CLIP 모델 로드
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Device: {device}")
        
        # safetensors=True 옵션 사용 (보안/속도)
        model = CLIPModel.from_pretrained(MODEL_ID, use_safetensors=True).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_ID, use_safetensors=True)
        
        ml_models["clip_model"] = model
        ml_models["clip_processor"] = processor
        ml_models["device"] = device
        logger.info("✅ CLIP 모델 로드 성공")
    except Exception as e:
        logger.error(f"❌ 모델 로드 실패: {e}")

    # 2. 벡터 DB (.pkl) 로드
    try:
        with open(VECTOR_DB_PATH, 'rb') as f:
            vector_data = pickle.load(f)
            # 검색 속도를 위해 ID 리스트와 벡터 배열 분리
            ml_models["db_ids"] = [item['id'] for item in vector_data]
            ml_models["db_vectors"] = np.array([item['vector'] for item in vector_data])
            logger.info(f"✅ 벡터 DB 로드 성공 ({len(ml_models['db_ids'])}개)")
    except Exception as e:
        logger.error(f"❌ 벡터 DB 로드 실패: {e}")

    yield 
    
    # 종료 시 리소스 정리
    ml_models.clear()
    logger.info("서버 종료")

app = FastAPI(lifespan=lifespan)

# --- CORS 설정 (프론트엔드 연동) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 정적 파일 서빙 (이미지) ---
app.mount("/static/images", StaticFiles(directory=PROJECT_ROOT / "data" / "images"), name="static_images")

# --- 헬퍼 함수 ---
def get_db_connection():
    """DB 연결 생성"""
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )

def save_search_log(search_type, query=None, filename=None):
    """검색 로그 저장"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO search_logs (search_type, query, filename) VALUES (%s, %s, %s)", 
                           (search_type, query, filename))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"로그 저장 실패: {e}")

# --- 데이터 모델 (Pydantic) ---
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class ProductResponse(BaseModel):
    id: str
    product_name: str | None = None
    description: str | None = None
    brand: str | None = None
    color: str | None = None
    size: str | None = None
    price: int | None = None  
    season: str | None = None
    image_file: str | None = None

# --- API 엔드포인트 ---

@app.get("/")
def read_root():
    return {"message": "Modify AI Search Engine"}

# (!!!) [API 1] 스마트 검색 (Watsonx - 프롬프트 강화)
@app.post("/search/smart", response_model=list[ProductResponse])
async def search_smart(request: SearchRequest):
    user_query = request.query
    
    # 로그 강제 출력 (디버깅용)
    print(f"\n\n====================================================", flush=True)
    print(f"🤖 [START] 스마트 검색 요청: '{user_query}'", flush=True)

    ai_keyword = user_query
    ai_season = None

    if WATSONX_API_KEY and WATSONX_PROJECT_ID:
        try:
            model = ModelInference(
                model_id="meta-llama/llama-3-70b-instruct",
                params={
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 200,
                    GenParams.STOP_SEQUENCES: ["}"]
                },
                credentials=Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY),
                project_id=WATSONX_PROJECT_ID
            )
            
            # (!!!) 프롬프트 강화: 한글 질문을 영어 시각적 묘사로 변환하도록 지시
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a professional fashion stylist AI.
Your task is to convert the user's request into a **concrete visual search query** in **ENGLISH** for the CLIP model.

[Rules]
1. **search_keyword**: Translate the core visual elements to **English**. (e.g., "빨간 패딩" -> "Red puffer jacket")
2. **season**: Extract season if mentioned or implied. Must be one of [봄, 여름, 가을, 겨울] or null.

[Examples]
- User: "크리스마스 데이트룩" -> Keyword: "Red wool coat, White knitted sweater, Winter romantic style", Season: "겨울"
- User: "남자 여름 코디" -> Keyword: "Men's short sleeve linen shirt, Beige shorts, Casual summer look", Season: "여름"

Respond ONLY in JSON format:
{{
    "search_keyword": "...",
    "season": "..."
}}
<|eot_id|><|start_header_id|>user<|end_header_id|>
{user_query}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
            generated_response = model.generate_text(prompt=prompt).strip()
            # JSON 파싱 보정
            if not generated_response.endswith("}"): generated_response += "}"
            
            llm_result = json.loads(generated_response)
            ai_keyword = llm_result.get("search_keyword", user_query)
            ai_season = llm_result.get("season")
            
            # (!!!) 로그 출력
            print(f"🧠 [Watson 분석 결과]", flush=True)
            print(f"   ▶ 원본 질문: {user_query}", flush=True)
            print(f"   ▶ 영어 변환: {ai_keyword}", flush=True)
            print(f"   ▶ 추출 계절: {ai_season}", flush=True)

        except Exception as e:
            print(f"❌ Watson 호출 실패: {e}", flush=True)

    # 벡터 검색 실행
    print(f"🚀 [Vector Search] '{ai_keyword}' 검색 시작...", flush=True)
    return perform_vector_search(ai_keyword, request.top_k, ai_season)


# (!!!) [API 2] 텍스트 검색 (단순 번역기 적용)
@app.post("/search/text", response_model=list[ProductResponse])
async def search_by_text(request: SearchRequest):
    save_search_log("text", query=request.query)
    
    # 한글 -> 영어 번역 (CLIP 성능 향상)
    translated_query = request.query
    try:
        translated_query = GoogleTranslator(source='auto', target='en').translate(request.query)
        logger.info(f"🌍 번역: '{request.query}' -> '{translated_query}'")
    except Exception:
        pass

    return perform_vector_search(translated_query, request.top_k)


# [API 3] 이미지 검색
@app.post("/search/image", response_model=list[ProductResponse])
async def search_by_image(file: UploadFile = File(...), top_k: int = 5):
    save_search_log("image", filename=file.filename)
    if "clip_model" not in ml_models: raise HTTPException(500, "AI 모델 미준비")
    
    try:
        image = Image.open(io.BytesIO(await file.read()))
        inputs = ml_models["clip_processor"](images=image, return_tensors="pt", padding=True).to(ml_models["device"])
        with torch.no_grad(): vector = ml_models["clip_model"].get_image_features(**inputs)
        vector_np = vector.squeeze().cpu().numpy().reshape(1, -1)
        return search_in_db(vector_np, top_k)
    except Exception as e:
        logger.error(f"이미지 처리 실패: {e}")
        raise HTTPException(500, "이미지 처리 실패")


# [API 4] 연관 상품
@app.get("/search/related/{item_id}", response_model=list[ProductResponse])
async def search_by_related(item_id: str, top_k: int = 5):
    save_search_log("related", query=item_id)
    if "db_ids" not in ml_models: raise HTTPException(500, "DB 미준비")
    
    try:
        idx = ml_models["db_ids"].index(item_id)
        vector_np = ml_models["db_vectors"][idx].reshape(1, -1)
        # 자기 자신 제외
        return search_in_db(vector_np, top_k, exclude_id=item_id)
    except ValueError:
        raise HTTPException(404, "상품 없음")


# [API 5] 상세 정보
@app.get("/product/{item_id}", response_model=ProductResponse)
async def get_product(item_id: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 모든 컬럼 조회
            sql = "SELECT id, product_name, description, brand, color, size, price, season, image_file FROM products WHERE id = %s"
            cursor.execute(sql, (item_id,))
            res = cursor.fetchone()
            if res: return res
            raise HTTPException(404, "상품 없음")
    finally: conn.close()


# [API 6] 로그 조회
@app.get("/admin/logs")
def get_logs():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM search_logs ORDER BY created_at DESC LIMIT 100")
            return cursor.fetchall()
    finally: conn.close()


# --- 공통 검색 로직 ---
def perform_vector_search(text, top_k, season_filter=None):
    if "clip_model" not in ml_models: raise HTTPException(500, "AI 미준비")
    try:
        inputs = ml_models["clip_processor"](text=[text], return_tensors="pt", padding=True).to(ml_models["device"])
        with torch.no_grad(): vector = ml_models["clip_model"].get_text_features(**inputs)
        vector_np = vector.squeeze().cpu().numpy().reshape(1, -1)
        return search_in_db(vector_np, top_k, season_filter=season_filter)
    except Exception as e:
        logger.error(f"벡터 변환 실패: {e}")
        raise HTTPException(500, "검색 실패")

def search_in_db(query_vector, top_k, exclude_id=None, season_filter=None):
    sims = cosine_similarity(query_vector, ml_models["db_vectors"])
    # 필터링을 위해 넉넉하게 후보 추출
    top_indices = np.argsort(sims[0])[-(top_k+100):][::-1]
    
    candidates = []
    for i in top_indices:
        if exclude_id and ml_models["db_ids"][i] == exclude_id: continue
        candidates.append(ml_models["db_ids"][i])
    
    if not candidates: return []

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(candidates))
            # 모든 컬럼 조회
            sql = f"SELECT id, product_name, description, brand, color, size, price, season, image_file FROM products WHERE id IN ({format_strings})"
            cursor.execute(sql, tuple(candidates))
            rows = cursor.fetchall()
            
            sorted_results = []
            id_map = {row['id']: row for row in rows}
            
            for cid in candidates:
                if cid in id_map:
                    item = id_map[cid]
                    # (!!!) 계절 필터링 (스마트 검색용)
                    if season_filter and item['season']:
                        # DB에 '가을, 겨울' 처럼 되어있을 수 있으므로 포함 여부 확인
                        if season_filter in item['season']:
                            sorted_results.append(item)
                    else:
                        # 계절 조건이 없으면 통과
                        sorted_results.append(item)
                if len(sorted_results) >= top_k: break
            
            return sorted_results
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)