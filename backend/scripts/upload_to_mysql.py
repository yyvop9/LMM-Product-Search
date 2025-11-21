import pandas as pd
import pymysql
import os
from pathlib import Path
import logging
from dotenv import load_dotenv
import re # 정규표현식 (가격 정제용)

# --- 0. 로깅 및 경로 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
BACKEND_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_ROOT.parent

load_dotenv(BACKEND_ROOT / ".env")

# --- 1. CSV 및 DB 설정 ---

# 파일 경로
CSV_PATH = PROJECT_ROOT / "data" / "products.csv"
DATA_SAMPLE_SIZE = 5000 # (원하는 만큼 설정)

# (!!!) CSV 헤더 매핑 (본인 CSV 파일 기준)
COL_ID = 'image_filename'
COL_NAME = 'product_name'
COL_DESC = 'description'
COL_BRAND = 'brand'
COL_COLOR = 'color'
COL_SIZE = 'size'
COL_PRICE = 'price'
COL_SEASON = 'season'
COL_IMAGE = 'image_filename'

# DB 접속 정보
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "12345") 
DB_NAME = os.environ.get("DB_NAME", "lmm_project")

def connect_db():
    try:
        connection = pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
            charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
        )
        logger.info(f"✅ MySQL '{DB_NAME}' 연결 성공!")
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"❌ MySQL 연결 실패: {e}")
        return None

def clean_price(price_str):
    """
    가격 데이터 정제 함수 (버그 수정됨)
    - 178000.0 (float 문자열) -> 178000 (int)
    - "178,000원" (문자열) -> 178000 (int)
    """
    if pd.isna(price_str):
        return 0
        
    try:
        # 1. 먼저 숫자로 변환 시도 (178000.0 같은 경우 처리)
        return int(float(price_str))
    except (ValueError, TypeError):
        # 2. 실패 시 문자열에서 숫자만 추출 ("178,000원")
        try:
            return int(re.sub(r'[^0-9]', '', str(price_str)))
        except:
            return 0 # 정말 알 수 없는 값이면 0원 처리

def upload_data(connection):
    try:
        # 인코딩 문제 방지 (utf-8-sig 시도 후 cp949)
        try:
            df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(CSV_PATH, encoding='cp949')
            
        logger.info(f"'{CSV_PATH}' 로드 성공. (총 {len(df)}개)")
    except FileNotFoundError:
        logger.error(f"❌ 에러: 파일을 찾을 수 없습니다: {CSV_PATH}")
        return

    # 데이터 샘플링
    df_sample = df.head(DATA_SAMPLE_SIZE)
    logger.info(f"데이터 {len(df_sample)}개 업로드 시작...")
    
    cursor = connection.cursor()
    insert_count = 0
    
    # 모든 컬럼 INSERT
    sql = f"""
        INSERT IGNORE INTO products 
        (id, product_name, description, brand, color, size, price, season, image_file)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for index, row in df_sample.iterrows():
        try:
            # 데이터 추출 및 정제
            p_id = str(row[COL_ID])
            p_name = str(row[COL_NAME])
            p_desc = str(row[COL_DESC])
            p_brand = str(row[COL_BRAND])
            p_color = str(row[COL_COLOR])
            p_size = str(row[COL_SIZE])
            
            # (!!!) 수정된 clean_price 함수 적용
            p_price = clean_price(row[COL_PRICE])
            
            p_season = str(row[COL_SEASON])
            p_image = str(row[COL_IMAGE])
            
            cursor.execute(sql, (p_id, p_name, p_desc, p_brand, p_color, p_size, p_price, p_season, p_image))
            insert_count += 1
            
        except Exception as e:
            # logger.warning(f"데이터 에러 ({index}): {e}")
            pass # 에러 난 행은 건너뜀

    try:
        connection.commit()
        logger.info("="*30)
        logger.info(f"🎉 성공! 총 {insert_count}개의 데이터를 업로드했습니다.")
        logger.info("="*30)
    except Exception as e:
        connection.rollback()
        logger.error(f"❌ 커밋 실패: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    conn = connect_db()
    if conn:
        upload_data(conn)