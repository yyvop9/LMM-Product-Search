import sys
import os
import csv
import uuid
import re
import pickle
import numpy as np
import torch
import time
from PIL import Image
from pathlib import Path
from transformers import CLIPProcessor, CLIPModel
import logging

# 상위 폴더(app)를 모듈 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Product
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- [경로 설정] ---
BASE_DIR = Path("/app") 
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
CSV_PATH = DATA_DIR / "products.csv"
VECTOR_DB_PATH = DATA_DIR / "product_vectors.pkl"

# --- [1. 카테고리 추론 (우선순위 적용)] ---
def infer_category(name):
    if not name: return "Etc"
    name = name.lower().replace(" ", "")
    
    if any(x in name for x in ["원피스", "드레스", "점프수트", "셋업", "수트", "투피스", "dress", "setup", "suit"]): return "Onepiece"
    elif any(x in name for x in ["무스탕", "코트", "패딩", "자켓", "재킷", "점퍼", "가디건", "베스트", "조끼", "파카", "블레이저", "바람막이", "플리스", "후리스", "야상", "coat", "jacket", "padding", "jumper", "cardigan", "vest", "fleece"]): return "Outer"
    elif any(x in name for x in ["바지", "팬츠", "슬랙스", "데님", "청바지", "조거", "스커트", "치마", "레깅스", "쇼츠", "트레이닝팬츠", "pants", "jeans", "skirt", "leggings", "shorts", "slacks"]): return "Bottom"
    elif any(x in name for x in ["티셔츠", "맨투맨", "후드", "셔츠", "니트", "스웨터", "블라우스", "탑", "나시", "폴로", "크롭", "t-shirt", "sweat", "hoodie", "knit", "shirt", "blouse", "top", "crop"]): return "Top"
    elif any(x in name for x in ["신발", "운동화", "구두", "부츠", "샌들", "스니커즈", "로퍼", "shoes", "boots", "sneakers"]): return "Shoes"
    elif any(x in name for x in ["가방", "백", "숄더백", "백팩", "bag", "backpack"]): return "Bag"
    elif any(x in name for x in ["모자", "벨트", "양말", "목도리", "안경", "cap", "hat", "belt"]): return "Acc"
    else: return "Etc"

# --- [2. 성별 추론] ---
def infer_gender(row):
    desc = str(row.get('description', '')).replace(" ", "")
    name = str(row.get('product_name', '')).replace(" ", "")
    
    if "남성용" in desc or "남성용" in name: return "Men"
    if "여성용" in desc or "여성용" in name: return "Women"
    
    is_women = any(x in desc + name for x in ["여성", "여자", "우먼", "레이디", "블라우스", "스커트", "치마", "원피스", "women", "lady"])
    is_men = any(x in desc + name for x in ["남성", "남자", "맨", "옴므", "men", "homme"])
    
    if is_women and not is_men: return "Women"
    if is_men and not is_women: return "Men"
    return "Unisex"

# --- [3. 계절 추론] ---
def infer_season(row):
    csv_season = str(row.get('season', '')).strip()
    if csv_season and csv_season.lower() != 'nan': return csv_season
    
    text = (str(row.get('description', '')) + " " + str(row.get('product_name', ''))).lower()
    if any(x in text for x in ["패딩", "기모", "울", "코트", "겨울", "무스탕", "퍼", "시어링", "winter", "padding"]): return "Winter"
    if any(x in text for x in ["린넨", "반팔", "여름", "쿨", "summer", "linen"]): return "Summer"
    if any(x in text for x in ["트렌치", "가디건", "봄", "가을", "spring", "autumn"]): return "Spring/Autumn"
    return "All"

def clean_price(price_str):
    if not price_str: return 0
    try: return int(float(price_str))
    except:
        try: return int(re.sub(r'[^0-9]', '', str(price_str)))
        except: return 0

def upload_data():
    logger.info("🚀 [Start] 데이터 로더 시작 (Progress Bar ver.)")
    
    logger.info("📥 [AI] CLIP 모델 로딩 중...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = "openai/clip-vit-large-patch14"
    model = CLIPModel.from_pretrained(model_id).to(device)
    processor = CLIPProcessor.from_pretrained(model_id)
    
    db: Session = SessionLocal()
    vector_data_list = []

    try:
        if not CSV_PATH.exists():
            logger.error(f"❌ CSV 파일 없음: {CSV_PATH}")
            return

        encoding = 'utf-8-sig'
        try:
            with open(CSV_PATH, 'r', encoding=encoding) as f: f.read()
        except UnicodeDecodeError:
            encoding = 'cp949'

        # 1. 전체 개수 세기 (Progress Bar용)
        total_rows = 0
        with open(CSV_PATH, 'r', encoding=encoding) as f:
            total_rows = sum(1 for row in csv.reader(f)) - 1 # 헤더 제외
        
        print(f"📊 총 처리 대상: {total_rows}건")

        with open(CSV_PATH, 'r', encoding=encoding) as f:
            csv_reader = csv.reader(f)
            raw_header = next(csv_reader)
            clean_header = [h.strip().replace('\ufeff', '') for h in raw_header]
            reader = csv.DictReader(f, fieldnames=clean_header)
            
            # 초기화
            db.query(Product).delete()
            db.commit()
            
            count = 0
            skipped = 0
            seen_ids = set()
            start_time = time.time()

            for row in reader:
                try:
                    image_filename = None
                    for key in ['image_filename', 'filename', 'image', 'file']:
                        if row.get(key):
                            image_filename = row.get(key).strip()
                            break
                    
                    if not image_filename: 
                        skipped += 1
                        continue

                    img_path = IMAGE_DIR / image_filename
                    if not img_path.exists():
                        skipped += 1
                        continue

                    p_id = row.get('id') or str(uuid.uuid4())
                    if p_id in seen_ids: continue
                    seen_ids.add(p_id)

                    p_name = row.get('product_name', '').strip() or 'No Name'
                    
                    # 추론
                    auto_category = infer_category(p_name)
                    auto_gender = infer_gender(row)
                    auto_season = infer_season(row)
                    p_price = clean_price(row.get('price'))

                    product = Product(
                        id=p_id,
                        product_name=p_name,
                        description=row.get('description', ''),
                        brand=row.get('brand', 'No Brand'),
                        color=row.get('color'),
                        size=row.get('size'),
                        price=p_price,
                        season=auto_season,
                        gender=auto_gender,
                        category=auto_category,
                        image_file=image_filename
                    )
                    db.merge(product)

                    # 벡터 생성
                    image = Image.open(img_path).convert("RGB")
                    inputs = processor(images=image, return_tensors="pt", padding=True).to(device)
                    with torch.no_grad():
                        vector = model.get_image_features(**inputs).squeeze().cpu().numpy()
                    
                    vector_data_list.append({"id": p_id, "vector": vector})
                    
                    count += 1
                    
                    # [진행률 표시 로직] 10개마다 로그 출력
                    if count % 10 == 0:
                        elapsed = time.time() - start_time
                        avg_time = elapsed / count
                        remain_time = (total_rows - count) * avg_time
                        percent = (count / total_rows) * 100
                        print(f"⏳ [{count}/{total_rows}] {percent:.1f}% 완료 | 남은시간: 약 {int(remain_time)}초 | 처리중: {p_name[:20]}...", flush=True)

                except Exception as e:
                    skipped += 1
                    continue
            
            db.commit()
            
            with open(VECTOR_DB_PATH, 'wb') as vf:
                pickle.dump(vector_data_list, vf)

            print("\n" + "="*40)
            print(f"🎉 작업 완료! (소요시간: {int(time.time() - start_time)}초)")
            print(f"✅ DB 저장: {count}건")
            print(f"✅ 벡터 생성: {len(vector_data_list)}건")
            print(f"⏭️ 스킵됨: {skipped}건")
            print("="*40)

    except Exception as e:
        logger.error(f"❌ 오류: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    upload_data()