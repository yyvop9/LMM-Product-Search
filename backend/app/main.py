import logging
import pickle
import os
import io
from pathlib import Path
from contextlib import asynccontextmanager

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
import json

# (!!!) 번역기 추가 (일반 검색용)
from deep_translator import GoogleTranslator

# IBM Watsonx 라이브러리
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# --- 0. 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).parent 
BACKEND_ROOT = APP_DIR.parent 
PROJECT_ROOT = BACKEND_ROOT.parent 
DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(BACKEND_ROOT / ".env")

ml_models = {}

# DB 정보
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "lmm_project")

MODEL_ID = "openai/clip-vit-base-patch32"
VECTOR_DB_PATH = DATA_DIR / "product_vectors.pkl"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("서버 시작... AI 모델 및 벡터 로드")
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Device: {device}")
        model = CLIPModel.from_pretrained(MODEL_ID, use_safetensors=True).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_ID, use_safetensors=True)
        ml_models["clip_model"] = model
        ml_models["clip_processor"] = processor
        ml_models["device"] = device
        logger.info("✅ CLIP 모델 로드 성공")
    except Exception as e:
        logger.error(f"❌ 모델 로드 실패: {e}")

    try:
        with open(VECTOR_DB_PATH, 'rb') as f:
            vector_data = pickle.load(f)
            ml_models["db_ids"] = [item['id'] for item in vector_data]
            ml_models["db_vectors"] = np.array([item['vector'] for item in vector_data])
            logger.info(f"✅ 벡터 DB 로드 성공 ({len(ml_models['db_ids'])}개)")
    except Exception as e:
        logger.error(f"❌ 벡터 DB 로드 실패: {e}")

    yield 
    ml_models.clear()
    logger.info("서버 종료")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/images", StaticFiles(directory=PROJECT_ROOT / "data" / "images"), name="static_images")

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )

def save_search_log(search_type, query=None, filename=None):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO search_logs (search_type, query, filename) VALUES (%s, %s, %s)", 
                           (search_type, query, filename))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"로그 저장 실패: {e}")

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

@app.get("/")
def read_root():
    return {"message": "Modify AI Search Engine"}

# (!!!) [핵심 1] 스마트 검색 (Watsonx - 스타일리스트 역할)
@app.post("/search/smart", response_model=list[ProductResponse])
async def search_smart(request: SearchRequest):
    user_query = request.query
    logger.info(f"🤖 스마트 검색 요청 (Watson): '{user_query}'")

    api_key = os.environ.get("WATSONX_API_KEY")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    url = os.environ.get("WATSONX_URL")

    ai_keyword = user_query
    ai_season = None

    if api_key and project_id:
        try:
            model = ModelInference(
                model_id="meta-llama/llama-3-70b-instruct",
                params={
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 200,
                    GenParams.STOP_SEQUENCES: ["}"]
                },
                credentials=Credentials(url=url, api_key=api_key),
                project_id=project_id
            )
            
            # (!!!) 프롬프트 강화: 무조건 영어로, 시각적 묘사로 변환하라고 지시
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a fashion stylist AI.
Translate the user's request into a **Detailed English Visual Description** optimized for CLIP image search.
If the user asks for a situation (e.g., "Christmas", "Date"), convert it to visual attributes (e.g., "Red dress", "Romantic style").

Target: Suggest items that visually match the description.
Respond ONLY in JSON format:
{{
    "search_keyword": "English visual description (e.g. Red winter wool coat)",
    "season": "Exact one of [봄, 여름, 가을, 겨울] or null"
}}
<|eot_id|><|start_header_id|>user<|end_header_id|>
{user_query}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
            res = model.generate_text(prompt=prompt).strip()
            if not res.endswith("}"): res += "}"
            parsed = json.loads(res)
            ai_keyword = parsed.get("search_keyword", user_query) # 영문 키워드
            ai_season = parsed.get("season")
            
            logger.info(f"🧠 Watson 전략: '{user_query}' -> '{ai_keyword}' (계절: {ai_season})")
        except Exception as e:
            logger.error(f"Watson 실패: {e}")

    return perform_vector_search(ai_keyword, request.top_k, ai_season)

# (!!!) [핵심 2] 일반 텍스트 검색 (단순 번역기 사용)
@app.post("/search/text", response_model=list[ProductResponse])
async def search_by_text(request: SearchRequest):
    save_search_log("text", query=request.query)
    
    # 한글 입력 -> 영어로 단순 번역 (CLIP 성능 향상용)
    try:
        translated_query = GoogleTranslator(source='auto', target='en').translate(request.query)
        logger.info(f"🌍 번역: '{request.query}' -> '{translated_query}'")
    except Exception:
        translated_query = request.query

    return perform_vector_search(translated_query, request.top_k)

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

@app.get("/search/related/{item_id}", response_model=list[ProductResponse])
async def search_by_related(item_id: str, top_k: int = 5):
    save_search_log("related", query=item_id)
    if "db_ids" not in ml_models: raise HTTPException(500, "DB 미준비")
    
    try:
        idx = ml_models["db_ids"].index(item_id)
        vector_np = ml_models["db_vectors"][idx].reshape(1, -1)
        return search_in_db(vector_np, top_k, exclude_id=item_id)
    except ValueError:
        raise HTTPException(404, "상품 없음")

@app.get("/product/{item_id}", response_model=ProductResponse)
async def get_product(item_id: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, product_name, description, brand, color, size, price, season, image_file FROM products WHERE id = %s"
            cursor.execute(sql, (item_id,))
            res = cursor.fetchone()
            if res: return res
            raise HTTPException(404, "상품 없음")
    finally: conn.close()

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
    # 넉넉하게 후보군 추출
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
            sql = f"SELECT id, product_name, description, brand, color, size, price, season, image_file FROM products WHERE id IN ({format_strings})"
            cursor.execute(sql, tuple(candidates))
            rows = cursor.fetchall()
            
            sorted_results = []
            id_map = {row['id']: row for row in rows}
            
            for cid in candidates:
                if cid in id_map:
                    item = id_map[cid]
                    # (!!!) 계절 필터링 (null 체크 포함)
                    if season_filter and item.get('season'):
                        # DB에 '가을, 겨울' 처럼 되어있을 수 있으므로 in 연산자 사용
                        if season_filter in item['season']:
                            sorted_results.append(item)
                    else:
                        # 계절 필터가 없거나, 상품에 계절 정보가 없으면 그냥 포함
                        sorted_results.append(item)
                if len(sorted_results) >= top_k: break
            
            return sorted_results
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)