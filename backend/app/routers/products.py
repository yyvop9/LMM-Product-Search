import os
import pickle
import shutil
import uuid
import json
import logging
import re
import random
import numpy as np
import torch
from PIL import Image
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from sklearn.metrics.pairwise import cosine_similarity
from transformers import CLIPProcessor, CLIPModel

# Watsonx
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from .. import database, models

# --- [설정 및 경로] ---
router = APIRouter(tags=["products"])
logger = logging.getLogger(__name__)

# [핵심] Docker 환경 절대 경로 고정
DATA_DIR = Path("/app/data")
IMAGE_DIR = DATA_DIR / "images"
VECTOR_DB_PATH = DATA_DIR / "product_vectors.pkl"

# 폴더 없으면 생성
if not IMAGE_DIR.exists():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# 전역 모델 저장소
ml_models = {}

# --- [Schemas] ---
class ProductResponse(BaseModel):
    id: str
    product_name: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[int] = None
    season: Optional[str] = None
    gender: Optional[str] = None 
    category: Optional[str] = None
    color: Optional[str] = None
    image_file: str
    class Config: from_attributes = True 

class SearchRequest(BaseModel):
    query: str
    top_k: int = 20
    sort_by: str = "relevance" 

class SmartSearchResponse(BaseModel):
    products: List[ProductResponse]
    debug_info: Dict[str, Any]

class CoordinationResponse(BaseModel):
    target_product: ProductResponse
    recommended_item: ProductResponse
    ai_comment: str
    match_score: int

# --- [Core 1] AI 모델 로드 ---
def load_ai_models():
    """서버 시작 시 main.py에서 호출됨"""
    logger.info(f"📥 [시스템] AI 모델 로드 시작... (경로: {VECTOR_DB_PATH})")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ml_models["device"] = device 
    
    # 1. CLIP 로드
    try:
        model_id = "openai/clip-vit-large-patch14"
        model = CLIPModel.from_pretrained(model_id).to(device)
        processor = CLIPProcessor.from_pretrained(model_id)
        
        ml_models["clip_model"] = model
        ml_models["clip_processor"] = processor
        logger.info(f"✅ [완료] CLIP 모델 로드 성공 (Device: {device})")
    except Exception as e:
        logger.error(f"❌ [에러] CLIP 로드 실패: {e}")

    # 2. 벡터 DB 로드
    try:
        if VECTOR_DB_PATH.exists():
            with open(VECTOR_DB_PATH, 'rb') as f:
                data = pickle.load(f)
                ml_models["db_ids"] = [str(item['id']) for item in data]
                ml_models["db_vectors"] = np.array([item['vector'] for item in data], dtype='float32')
                ml_models["id_to_index"] = {pid: i for i, pid in enumerate(ml_models["db_ids"])}
                logger.info(f"✅ [완료] 벡터 데이터 로드 성공 (총 {len(ml_models['db_ids'])}건)")
        else:
            logger.warning(f"⚠️ [주의] 벡터 파일이 없습니다. 빈 상태로 시작합니다.")
            ml_models["db_ids"] = []
            ml_models["db_vectors"] = np.empty((0, 768))
            ml_models["id_to_index"] = {}
    except Exception as e:
        logger.error(f"❌ [에러] 벡터 DB 로드 실패: {e}")

def save_vector_index():
    try:
        data = []
        for i, pid in enumerate(ml_models["db_ids"]):
            data.append({"id": pid, "vector": ml_models["db_vectors"][i]})
        with open(VECTOR_DB_PATH, 'wb') as f:
            pickle.dump(data, f)
        ml_models["id_to_index"] = {pid: i for i, pid in enumerate(ml_models["db_ids"])}
    except Exception as e:
        logger.error(f"Vector Save Failed: {e}")

# --- [Core 2] 임베딩 생성 ---
def get_embedding(text=None, image_path=None):
    if not ml_models.get("clip_model"):
        logger.error("AI 모델 미로드 상태")
        return None

    device = ml_models["device"]
    model = ml_models["clip_model"]
    processor = ml_models["clip_processor"]
    
    with torch.no_grad():
        if text:
            inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(device)
            vector = model.get_text_features(**inputs)
        elif image_path:
            image = Image.open(image_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt", padding=True).to(device)
            vector = model.get_image_features(**inputs)
        else:
            return None
            
    return vector.squeeze().cpu().numpy().reshape(1, -1)

# --- [Core 3] Hybrid Search Logic (한글 로그 & Fallback) ---
def hybrid_search(query_vector, top_k, db: Session, filters: Dict[str, Any] = None, sort_by: str = "relevance"):
    if len(ml_models.get("db_ids", [])) == 0:
        return [], "No Data"

    query = db.query(models.Product)
    
    # DB 체크
    total_count = query.count()
    if total_count == 0:
        logger.warning("⚠️ [DB 경고] 데이터베이스가 비어있습니다!")
        return [], "Empty DB"

    # 1. 필터 적용
    is_filtered = False
    if filters:
        if filters.get("gender") and filters["gender"] != "Unisex":
            query = query.filter(or_(models.Product.gender == filters["gender"], models.Product.gender == "Unisex"))
            is_filtered = True
        if filters.get("category"):
            query = query.filter(models.Product.category == filters["category"])
            is_filtered = True
        if filters.get("season"):
            query = query.filter(models.Product.season.contains(filters["season"]))
            is_filtered = True
        if filters.get("min_price"):
            query = query.filter(models.Product.price >= filters["min_price"])
            is_filtered = True
        if filters.get("max_price"):
            query = query.filter(models.Product.price <= filters["max_price"])
            is_filtered = True
        if filters.get("brand"):
             query = query.filter(models.Product.brand.contains(filters["brand"]))
             is_filtered = True

    candidates = query.all()
    search_mode = "Strict Filter"
    
    # [로그] 필터링 결과 출력
    filter_info = json.dumps(filters, ensure_ascii=False) if filters else "없음"
    logger.info(f"🔍 [검색 실행] 1차 필터링 결과: {len(candidates)}건 (적용 필터: {filter_info})")

    # 2. [핵심] Fallback Logic: 결과 3개 미만이면 필터 해제
    if len(candidates) < 3:
        logger.info(f"🔄 [자동 재검색] 결과가 부족하여({len(candidates)}건), 필터를 해제하고 전체 검색을 시도합니다.")
        search_mode = "Fallback (Vector Only)"
        candidates = db.query(models.Product).all()
        logger.info(f"   ㄴ 전체 검색 후보: {len(candidates)}건 확보")

    if not candidates:
        logger.info("❌ [검색 실패] 조건에 맞는 상품이 없습니다.")
        return [], "No Results"

    # 3. 벡터 매칭
    candidate_ids = [p.id for p in candidates]
    target_indices = []
    valid_candidates = []
    
    for pid, product in zip(candidate_ids, candidates):
        idx = ml_models.get("id_to_index", {}).get(pid)
        if idx is not None:
            target_indices.append(idx)
            valid_candidates.append(product)
            
    if not target_indices:
        return [], "Vector Mismatch"

    target_vectors = ml_models["db_vectors"][target_indices]
    sims = cosine_similarity(query_vector, target_vectors)[0]
    
    results_with_score = []
    for i, score in enumerate(sims):
        results_with_score.append({"product": valid_candidates[i], "score": score})
        
    # 4. 정렬
    if sort_by == "price_asc":
        results_with_score.sort(key=lambda x: x["product"].price if x["product"].price else float('inf'))
    elif sort_by == "price_desc":
        results_with_score.sort(key=lambda x: x["product"].price if x["product"].price else 0, reverse=True)
    else:
        results_with_score.sort(key=lambda x: x["score"], reverse=True)

    return [item["product"] for item in results_with_score[:top_k]], search_mode

# --- [API Endpoints] ---

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
    gender: str = Form(None),
    category: str = Form(None),
    db: Session = Depends(database.get_db)
):
    product_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1]
    filename = f"{product_id}.{ext}"
    file_path = IMAGE_DIR / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        vector = get_embedding(image_path=file_path)
        if vector is None: vector = np.zeros((1, 768))
        
        new_product = models.Product(
            id=product_id, product_name=product_name, description=description,
            brand=brand, color=color, size=size, price=price, season=season,
            gender=gender, category=category, image_file=filename
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        ml_models["db_ids"].append(product_id)
        if len(ml_models["db_vectors"]) == 0:
             ml_models["db_vectors"] = vector
        else:
             ml_models["db_vectors"] = np.vstack([ml_models["db_vectors"], vector])
        
        save_vector_index()
        return {"message": "Success", "id": product_id}
        
    except Exception as e:
        if file_path.exists(): file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product: raise HTTPException(404, "Product not found")
    
    file_path = IMAGE_DIR / product.image_file; 
    if file_path.exists(): file_path.unlink()
    
    db.delete(product)
    db.commit()
    
    if product_id in ml_models.get("id_to_index", {}):
        idx = ml_models["id_to_index"][product_id]
        ml_models["db_ids"].pop(idx)
        ml_models["db_vectors"] = np.delete(ml_models["db_vectors"], idx, axis=0)
        save_vector_index()
        
    return None

@router.post("/search/text", response_model=List[ProductResponse])
def search_text(req: SearchRequest, db: Session = Depends(database.get_db)):
    query_en = req.query
    try:
        query_en = GoogleTranslator(source='auto', target='en').translate(req.query)
    except: pass
    
    vector = get_embedding(text=query_en)
    if vector is None: raise HTTPException(500, "AI Service Error")
    
    results, _ = hybrid_search(vector, req.top_k, db, filters=None, sort_by=req.sort_by)
    return results

@router.post("/search/image", response_model=List[ProductResponse])
async def search_image(file: UploadFile = File(...), top_k: int = 5, db: Session = Depends(database.get_db)):
    contents = await file.read()
    temp_path = Path(f"temp_{uuid.uuid4()}.jpg")
    with open(temp_path, "wb") as f:
        f.write(contents)
    try:
        vector = get_embedding(image_path=temp_path)
        if vector is None: raise HTTPException(500, "AI Service Error")
        results, _ = hybrid_search(vector, top_k, db, filters=None)
    finally:
        if temp_path.exists(): temp_path.unlink()
    return results

@router.post("/search/smart", response_model=SmartSearchResponse)
def search_smart(req: SearchRequest, db: Session = Depends(database.get_db)):
    user_query = req.query
    wx_key = os.getenv("WATSONX_API_KEY")
    wx_url = os.getenv("WATSONX_URL")
    wx_pid = os.getenv("WATSONX_PROJECT_ID")
    
    filters = {}
    visual_keyword = user_query
    
    # 1. Watsonx LLM Logic
    if wx_key and wx_pid:
        try:
            model = ModelInference(
                model_id="meta-llama/llama-3-3-70b-instruct",
                params={GenParams.DECODING_METHOD: "greedy", GenParams.MAX_NEW_TOKENS: 600},
                credentials=Credentials(url=wx_url, api_key=wx_key),
                project_id=wx_pid
            )
            
            # [Ultimate Prompt] 맥락/가격/계절 완벽 이해
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an elite AI Fashion Stylist. Analyze the Korean query deeply and extract precise JSON filters.

[RULE 1: GENDER & CONTEXT]
- Relationships: "남자친구/남편/아빠"(Boyfriend/Husband/Dad) -> User is Female looking for Male clothes -> Set "gender": "Women"
- Relationships: "여자친구/아내/엄마"(Girlfriend/Wife/Mom) -> User is Male looking for Female clothes -> Set "gender": "Men"
- Terminology: "보이프렌드 핏/맘핏"(Boyfriend/Mom fit) -> These are WOMEN'S styles -> Set "gender": "Women"
- Override: Explicit "남자/남성"(Men's) or "여자/여성"(Women's) keywords have highest priority.

[RULE 2: CATEGORY DISAMBIGUATION]
- "셔츠 원피스"(Shirt Dress) -> It is a Dress, NOT a Shirt -> Set "category": "Onepiece"
- "후드 집업/바람막이"(Zip-up/Windbreaker) -> Set "category": "Outer"
- "레깅스/조거"(Leggings/Joggers) -> Set "category": "Bottom"
- "셋업/수트"(Setup/Suit) -> Set "category": "Outer"

[RULE 3: SEASONAL PARADOX]
- "여름 니트"(Summer Knit) -> Material is knit but season is Summer -> Set "season": "Summer"
- "겨울 반바지"(Winter Shorts) -> Item is shorts but material is wool/corduroy -> Set "season": "Winter"
- Always prioritize the explicit season keyword over the item's typical season.

[RULE 4: PRICE MAPPING (KRW)]
- "싼/저렴한/가성비"(Cheap/Budget) -> Set "max_price": 50000
- "비싼/명품/프리미엄"(Expensive/Luxury) -> Set "min_price": 100000
- "적당한/무난한"(Reasonable) -> Set "min_price": 30000, "max_price": 100000

[RULE 5: VISUAL KEYWORD OPTIMIZATION]
- Remove non-visual words like "추천해줘", "찾아줘", "입을거".
- Keep colors, patterns, materials, and style names (e.g., "Vintage", "Street", "Minimal").
- Example: "여름에 입을 시원한 파란색 린넨 셔츠 추천" -> "visual_keyword": "파란색 린넨 셔츠"

Query: "{user_query}"
Schema: {{ "gender": "Men"|"Women"|"Unisex"|null, "category": "Top"|"Bottom"|"Outer"|"Onepiece"|"Shoes"|"Bag"|"Acc"|null, "season": "Spring"|"Summer"|"Autumn"|"Winter"|null, "min_price": int|null, "max_price": int|null, "visual_keyword": str }}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
{{"""
            generated = model.generate_text(prompt=prompt).strip()
            
            # [로그] 한글로 AI 생각 출력
            logger.info(f"🤖 [AI 분석] Watsonx 응답:\n{generated}")

            # [안전한 JSON 파싱]
            try:
                clean_text = generated.replace("```json", "").replace("```", "").strip()
                if clean_text.startswith("{"): full_json = clean_text
                else: full_json = "{" + clean_text

                match = re.search(r'\{.*\}', full_json, re.DOTALL)
                if match: full_json = match.group()
                
                parsed = json.loads(full_json)
                filters = parsed
                visual_keyword = parsed.get("visual_keyword")
                
                # 시각적 키워드가 없으면 사용자 검색어 그대로 사용
                if not visual_keyword:
                    visual_keyword = user_query
                
                logger.info(f"✅ [파싱 성공] 필터: {filters} / 키워드: {visual_keyword}")
            
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ [파싱 실패] 기본 검색으로 전환합니다. (Error: {e})")
                visual_keyword = user_query
                
        except Exception as e:
            logger.error(f"❌ [AI 에러] Watsonx 연결 실패: {e}")
            visual_keyword = user_query

    # 2. Embedding & Search
    final_query_text = visual_keyword
    try:
         if final_query_text == user_query:
             final_query_text = GoogleTranslator(source='auto', target='en').translate(user_query)
    except: pass

    vector = get_embedding(text=final_query_text)
    if vector is None: raise HTTPException(500, "AI Error")

    results, search_mode = hybrid_search(vector, req.top_k, db, filters=filters, sort_by=req.sort_by)
    
    return {
        "products": results,
        "debug_info": { "query": user_query, "visual_keyword": final_query_text, "filters": filters, "mode": search_mode }
    }

@router.get("/product/{product_id}", response_model=ProductResponse)
def get_product_detail(product_id: str, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product: raise HTTPException(404, "Not found")
    return product

@router.get("/search/related/{product_id}", response_model=List[ProductResponse])
def get_related_products(product_id: str, top_k: int = 6, db: Session = Depends(database.get_db)):
    if product_id not in ml_models.get("id_to_index", {}): return []
    idx = ml_models["id_to_index"][product_id]
    vector = ml_models["db_vectors"][idx].reshape(1, -1)
    results, _ = hybrid_search(vector, top_k + 5, db, filters=None)
    final = [p for p in results if str(p.id) != str(product_id)][:top_k]
    return final

@router.get("/coordinate/{product_id}", response_model=List[CoordinationResponse])
def recommend_coordination(product_id: str, db: Session = Depends(database.get_db)):
    target = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not target: raise HTTPException(404, "Product not found")

    t_cat = (target.category or "").lower()
    recommend_cats = ["Bottom"]
    if "top" in t_cat: recommend_cats = ["Bottom"]
    elif "bottom" in t_cat: recommend_cats = ["Top", "Outer"]
    elif "outer" in t_cat: recommend_cats = ["Top", "Bottom"]

    gender_filter = [target.gender, "Unisex"] if target.gender else ["Men", "Women", "Unisex"]
    
    candidates = db.query(models.Product).filter(
        models.Product.gender.in_(gender_filter),
        models.Product.category.in_(recommend_cats),
        models.Product.id != target.id
    ).order_by(func.random()).limit(3).all()
    
    if not candidates:
         candidates = db.query(models.Product).filter(models.Product.id != target.id).order_by(func.random()).limit(3).all()

    results = []
    for item in candidates:
        results.append({
            "target_product": target,
            "recommended_item": item,
            "ai_comment": "이 아이템과 함께 매치해보세요! 세련된 스타일이 완성됩니다.",
            "match_score": random.randint(85, 98)
        })
    return results

@router.get("/recommendations/personal", response_model=List[ProductResponse])
def get_personalized_recommendations(db: Session = Depends(database.get_db), limit: int = 4):
    user_id = 1
    wishlist_items = db.query(models.Wishlist).filter(models.Wishlist.user_id == user_id).all()
    wish_pids = [item.product_id for item in wishlist_items]
    
    if not wish_pids or not ml_models.get("db_ids"):
        return db.query(models.Product).order_by(func.random()).limit(limit).all()
        
    target_vectors = []
    for pid in wish_pids:
        idx = ml_models.get("id_to_index", {}).get(pid)
        if idx is not None: target_vectors.append(ml_models["db_vectors"][idx])
            
    if not target_vectors: return []
    user_vector = np.mean(target_vectors, axis=0).reshape(1, -1)
    results, _ = hybrid_search(user_vector, top_k=limit+5, db=db, filters={})
    
    final = [p for p in results if p.id not in wish_pids][:limit]
    return final

@router.get("/debug/ai-status")
def debug_ai_status(db: Session = Depends(database.get_db)):
    """AI 모델 및 데이터 경로 상태 확인"""
    db_count = db.query(models.Product).count()
    status = {
        "clip_model_loaded": ml_models.get("clip_model") is not None,
        "vector_db_count": len(ml_models.get("db_ids", [])),
        "mysql_db_count": db_count, 
        "vector_db_path": str(VECTOR_DB_PATH),
        "path_exists": VECTOR_DB_PATH.exists(),
        "device": ml_models.get("device", "unknown")
    }
    return status