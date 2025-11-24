import sys
import os
import csv
import uuid
import re # 정규표현식
from pathlib import Path
import logging

# --- [중요] 상위 폴더(backend)를 파이썬 경로에 추가 ---
# scripts 폴더에서 app 모듈을 불러오기 위함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Product
from sqlalchemy.orm import Session

# --- 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "products.csv"

# --- [Logic] 가격 정제 함수 (네 코드를 이식함) ---
def clean_price(price_str):
    """
    가격 데이터 정제
    - 178000.0 -> 178000
    - "178,000원" -> 178000
    """
    if not price_str: return 0
    
    try:
        # 1. 실수형 문자열 처리
        return int(float(price_str))
    except (ValueError, TypeError):
        # 2. 특수문자 제거 후 처리
        try:
            return int(re.sub(r'[^0-9]', '', str(price_str)))
        except:
            return 0

# --- [Main] 데이터 업로드 ---
def upload_data():
    logger.info("🔄 데이터 업로드 시작 (SQLAlchemy Version)...")
    
    # DB 세션 생성 (database.py 설정 사용)
    db: Session = SessionLocal()
    
    try:
        if not CSV_PATH.exists():
            logger.error(f"❌ 파일 없음: {CSV_PATH}")
            return

        # 인코딩 자동 감지 로직 (utf-8-sig -> cp949)
        encoding = 'utf-8-sig'
        try:
            with open(CSV_PATH, 'r', encoding=encoding) as f: f.read()
        except UnicodeDecodeError:
            encoding = 'cp949'

        with open(CSV_PATH, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            
            count = 0
            skipped = 0
            
            for row in reader:
                try:
                    # 1. ID 처리 (CSV에 있으면 쓰고, 없으면 UUID 생성)
                    # 네 CSV 컬럼명: image_filename을 ID로 쓸지 결정 필요
                    # 여기서는 'image_filename'이 고유하다면 ID로 사용, 아니면 UUID
                    p_id = row.get('image_filename') 
                    if not p_id: p_id = str(uuid.uuid4())

                    # 2. 중복 확인 (이미 있으면 건너뜀)
                    exist = db.query(Product).filter(Product.id == p_id).first()
                    if exist:
                        skipped += 1
                        continue

                    # 3. 모델 객체 생성
                    product = Product(
                        id=p_id,
                        product_name=row.get('product_name'),
                        description=row.get('description'),
                        brand=row.get('brand'),
                        color=row.get('color'),
                        size=row.get('size'),
                        price=clean_price(row.get('price')), # 가격 정제 적용
                        season=row.get('season'),
                        image_file=row.get('image_filename') # 파일명 매핑
                    )
                    
                    db.add(product)
                    count += 1
                    
                    # 100개마다 로그
                    if count % 100 == 0:
                        logger.info(f"running... {count}개 처리 중")

                except Exception as row_err:
                    logger.warning(f"⚠️ 행 처리 중 에러: {row_err}")
                    continue
            
            db.commit()
            logger.info("="*30)
            logger.info(f"🎉 업로드 완료!")
            logger.info(f"✅ 성공: {count}개")
            logger.info(f"⏭️ 스킵(중복): {skipped}개")
            logger.info("="*30)

    except Exception as e:
        logger.error(f"❌ 스크립트 에러: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    upload_data()