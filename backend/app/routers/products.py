import os
import pickle
import shutil
import uuid
import json
import logging
import numpy as np
import torch
from PIL import Image
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from sklearn.metrics.pairwise import cosine_similarity
from transformers import CLIPProcessor, CLIPModel

# Watsonx (IBM)
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# 내부 모듈 임포트
from .. import database, models

# --- 설정 ---
router = APIRouter(tags=["products"])
logger = logging.getLogger(__name__)

# 경로 설정 (상위 폴더로 이동하여 data 찾기)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent # backend 상위
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
VECTOR_DB_PATH = DATA_DIR / "product_vectors.pkl"

# AI 모델 전역 변수 (Memory)
ml_models = {}

# --- Pydantic 스키마 (응답용) ---
class ProductResponse(BaseModel):
    id: str
    product_name: Optional[str]
    description: Optional[str]
    brand: Optional[str]
    price: Optional[int]
    season: Optional[str]
    image_file: str
    
    class Config:
        from_attributes = True # ORM 객체 매핑 허용

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

# --- [Core] AI 모델 로드 및 초기화 ---
def load_ai_models():
    """서버 시작 시 호출되어 모델을 메모리에 올림"""
    logger.info("📥 AI 모델 및 벡터 로드 시작...")
    
    # 디바이스 설정 (초기화)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ml_models["device"] = device 
    
    # 1. CLIP 로드
    try:
        model_id = "openai/clip-vit-large-patch14"
        
        # safetensors=True 옵션 사용 (보안 에러 해결)
        model = CLIPModel.from_pretrained(model_id, use_safetensors=True).to(device)
        processor = CLIPProcessor.from_pretrained(model_id, use_safetensors=True)
        
        ml_models["clip_model"] = model
        ml_models["clip_processor"] = processor
        logger.info(f"✅ CLIP Model Loaded (Device: {device})")
        
    except Exception as e:
        logger.error(f"❌ CLIP 로드 실패: {e}")
        # 실패하더라도 서버가 죽지 않도록 None 처리
        ml_models["clip_model"] = None
        ml_models["clip_processor"] = None

    # 2. 벡터 DB (.pkl) 로드
    try:
        if VECTOR_DB_PATH.exists():
            with open(VECTOR_DB_PATH, 'rb') as f:
                data = pickle.load(f)
                ml_models["db_ids"] = [item['id'] for item in data]
                ml_models["db_vectors"] = np.array([item['vector'] for item in data])
                logger.info(f"✅ Vector Index Loaded ({len(ml_models['db_ids'])} items)")
        else:
            logger.warning("⚠️ 벡터 파일이 없습니다. 빈 상태로 시작합니다.")
            ml_models["db_ids"] = []
            ml_models["db_vectors"] = np.empty((0, 512))
    except Exception as e:
        logger.error(f"❌ 벡터 DB 로드 실패: {e}")

# --- [Helper] 벡터 저장 및 검색 로직 ---
def save_vector_index():
    """메모리 상의 벡터를 파일로 영구 저장"""
    try:
        data = []
        for i, pid in enumerate(ml_models["db_ids"]):
            data.append({"id": pid, "vector": ml_models["db_vectors"][i]})
        with open(VECTOR_DB_PATH, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        logger.error(f"벡터 저장 실패: {e}")

def get_embedding(text=None, image_path=None):
    """CLIP을 사용하여 텍스트 또는 이미지의 임베딩 생성"""
    if not ml_models.get("clip_model"):
        logger.error("AI 모델이 로드되지 않았습니다.")
        raise HTTPException(status_code=503, detail="AI Service Unavailable")

    device = ml_models["device"]
    model = ml_models["clip_model"]
    processor = ml_models["clip_processor"]
    
    with torch.no_grad():
        if text:
            inputs = processor(text=[text], return_tensors="pt", padding=True).to(device)
            vector = model.get_text_features(**inputs)
        elif image_path:
            image = Image.open(image_path)
            inputs = processor(images=image, return_tensors="pt", padding=True).to(device)
            vector = model.get_image_features(**inputs)
        else:
            return None
            
    return vector.squeeze().cpu().numpy().reshape(1, -1)

def search_vectors(query_vector, top_k, db: Session, season_filter=None):
    """코사인 유사도 검색 + DB 메타데이터 필터링"""
    if len(ml_models["db_ids"]) == 0:
        return []

    # 1. 코사인 유사도 계산
    sims = cosine_similarity(query_vector, ml_models["db_vectors"])
    top_indices = np.argsort(sims[0])[::-1] # 내림차순 정렬
    
    results = []
    count = 0
    
    # 2. 순차적으로 DB 조회하며 필터링
    for idx in top_indices:
        pid = ml_models["db_ids"][idx]
        product = db.query(models.Product).filter(models.Product.id == pid).first()
        
        if not product: continue # 벡터엔 있는데 DB엔 없는 경우

        # 계절 필터 (스마트 검색용)
        if season_filter and product.season:
            if season_filter not in product.season:
                continue 

        results.append(product)
        count += 1
        if count >= top_k: break
        
    return results

# --- [API] 1. 상품 등록 (CRUD - Create) ---
@router.post("/products", status_code=201)
async def create_product(
    file: UploadFile = File(...),
    product_name: str = Form(...),
    description: str = Form(None),
    brand: str = Form(None),
    season: str = Form(None),
    price: int = Form(0),
    color: str = Form(None),
    size: str = Form(None),
    db: Session = Depends(database.get_db)
):
    # 1. UUID 및 파일 저장
    product_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1]
    filename = f"{product_id}.{ext}"
    file_path = IMAGE_DIR / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. 벡터 생성
        vector = get_embedding(image_path=file_path)
        
        # 3. DB 저장
        new_product = models.Product(
            id=product_id,
            product_name=product_name,
            description=description,
            brand=brand,
            color=color,
            size=size,
            price=price,
            season=season,
            image_file=filename
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        # 4. 벡터 인덱스 업데이트
        ml_models["db_ids"].append(product_id)
        if len(ml_models["db_vectors"]) == 0:
             ml_models["db_vectors"] = vector
        else:
             ml_models["db_vectors"] = np.vstack([ml_models["db_vectors"], vector])
        
        save_vector_index()
        
        return {"message": "Product created successfully", "id": product_id}

    except Exception as e:
        if file_path.exists(): file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

# --- [API] 2. 상품 삭제 (CRUD - Delete) ---
@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # 1. 파일 삭제
    file_path = IMAGE_DIR / product.image_file
    if file_path.exists():
        file_path.unlink()
        
    # 2. DB 삭제
    db.delete(product)
    db.commit()
    
    # 3. 벡터 인덱스 삭제
    if product_id in ml_models["db_ids"]:
        idx = ml_models["db_ids"].index(product_id)
        del ml_models["db_ids"][idx]
        ml_models["db_vectors"] = np.delete(ml_models["db_vectors"], idx, axis=0)
        save_vector_index()
        
    return None

# --- [API] 3. 텍스트 검색 ---
@router.post("/search/text", response_model=List[ProductResponse])
def search_text(req: SearchRequest, db: Session = Depends(database.get_db)):
    query_en = req.query
    try:
        query_en = GoogleTranslator(source='auto', target='en').translate(req.query)
    except: pass
    
    vector = get_embedding(text=query_en)
    return search_vectors(vector, req.top_k, db)

# --- [API] 4. 이미지 검색 ---
@router.post("/search/image", response_model=List[ProductResponse])
async def search_image(file: UploadFile = File(...), top_k: int = 5, db: Session = Depends(database.get_db)):
    contents = await file.read()
    temp_path = Path(f"temp_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(contents)
        
    try:
        vector = get_embedding(image_path=temp_path)
        results = search_vectors(vector, top_k, db)
    finally:
        if temp_path.exists(): temp_path.unlink()
        
    return results

# --- [API] 5. 스마트 검색 (Watsonx) ---
@router.post("/search/smart", response_model=List[ProductResponse])
def search_smart(req: SearchRequest, db: Session = Depends(database.get_db)):
    user_query = req.query
    
    wx_key = os.getenv("WATSONX_API_KEY")
    wx_url = os.getenv("WATSONX_URL")
    wx_pid = os.getenv("WATSONX_PROJECT_ID")
    
    ai_keyword = user_query
    ai_season = None
    
    if wx_key and wx_pid:
        try:
            model = ModelInference(
                model_id="meta-llama/llama-3-70b-instruct",
                params={GenParams.MAX_NEW_TOKENS: 200, GenParams.STOP_SEQUENCES: ["}"]},
                credentials=Credentials(url=wx_url, api_key=wx_key),
                project_id=wx_pid
            )
            
            prompt = f"""Convert user query to JSON for fashion search.
Query: "{user_query}"
Format: {{"search_keyword": "English Visual Description", "season": "봄/여름/가을/겨울 or null"}}
JSON:"""
            
            res = model.generate_text(prompt=prompt).strip()
            if not res.endswith("}"): res += "}"
            parsed = json.loads(res)
            ai_keyword = parsed.get("search_keyword", user_query)
            ai_season = parsed.get("season")
            logger.info(f"🧠 Smart Search: {ai_keyword} / {ai_season}")
            
        except Exception as e:
            logger.error(f"Watson Error: {e}")
            
    vector = get_embedding(text=ai_keyword)
    return search_vectors(vector, req.top_k, db, season_filter=ai_season)

# --- [API] 6. 상품 상세 조회 (ID로 조회) ---
# (!!!) 상세 페이지용 핵심 API
@router.get("/product/{product_id}", response_model=ProductResponse)
def get_product_detail(product_id: str, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# --- [API] 7. 연관 상품 추천 (벡터 유사도 기반) ---
# (!!!) 상세 페이지 하단 추천용 API
@router.get("/search/related/{product_id}", response_model=List[ProductResponse])
def get_related_products(product_id: str, top_k: int = 6, db: Session = Depends(database.get_db)):
    # 1. 대상 상품 존재 확인
    target = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # 2. 벡터가 로드되었는지 확인
    if not ml_models.get("db_ids"):
        return []

    # 3. 메모리에서 벡터 찾기
    try:
        if product_id in ml_models["db_ids"]:
            idx = ml_models["db_ids"].index(product_id)
            target_vector = ml_models["db_vectors"][idx].reshape(1, -1)
            
            # 4. 유사도 검색 (자기 자신 제외 로직 포함)
            # 넉넉하게 top_k + 5개를 가져온 뒤, 자기 자신을 리스트에서 뺌
            results = search_vectors(target_vector, top_k + 5, db)
            
            # 자기 자신(ID가 같은 것) 제외 필터링
            final_results = [p for p in results if str(p.id) != str(product_id)][:top_k]
            return final_results
    except ValueError:
        pass # 벡터가 없으면 빈 리스트 반환
    
    return []