import pandas as pd
import pymysql
import os
from pathlib import Path
import logging
from dotenv import load_dotenv # .env 파일 로드용

# --- 0. 로깅 및 경로 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 이 스크립트(backend/scripts/)의 상위 폴더(backend/)를 기준으로 .env 파일 로드
SCRIPT_DIR = Path(__file__).parent
BACKEND_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_ROOT.parent

# (중요!) .env 파일 위치 지정 (backend/.env)
load_dotenv(BACKEND_ROOT / ".env")

# --- 1. CSV 및 DB 설정 (!!! 여기를 수정하세요 !!!) ---

# (1) CSV 파일 경로
# (!!!) data.csv, styles.csv 등 실제 파일 이름으로 수정!
CSV_PATH = PROJECT_ROOT / "data" / "products.csv"
DATA_SAMPLE_SIZE = 500 # 업로드할 개수

# (2) CSV에서 읽어올 실제 컬럼 이름
# (!!!) products.csv 파일을 열어보고 실제 컬럼 이름으로 수정!
ID_COLUMN = 'image'         # 예: 'image' 또는 'id'
NAME_COLUMN = 'display name'  # 예: 'display_name' 또는 'productName'
DESC_COLUMN = 'description'   # 예: 'description'
IMAGE_COLUMN = 'image'        # 예: 'image' (id와 동일하게 사용)

# (3) DB 접속 정보 (backend/.env 파일에서 읽어옴)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "your_password") # .env에 꼭 설정!
DB_NAME = os.environ.get("DB_NAME", "lmm_project") # 위 SQL에서 만든 DB 이름

def connect_db():
    """MySQL 데이터베이스에 연결합니다."""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.info(f"✅ MySQL '{DB_NAME}' 데이터베이스 연결 성공!")
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"❌ MySQL 연결 실패: {e}")
        return None

def upload_data(connection):
    """CSV에서 데이터 500개를 읽어 DB에 INSERT합니다."""
    
    # --- 1. CSV 읽기 ---
    try:
        df = pd.read_csv(CSV_PATH)
        logger.info(f"'{CSV_PATH}' 파일 로드 성공. (총 {len(df)}개)")
    except FileNotFoundError:
        logger.error(f"❌ 에러: '{CSV_PATH}' 파일을 찾을 수 없습니다. 경로를 확인하세요.")
        return
    except KeyError:
        logger.error(f"❌ 에러: CSV 컬럼명(ID_COLUMN 등)이 잘못되었습니다. 스크립트를 확인하세요.")
        return
        
    df_sample = df.head(DATA_SAMPLE_SIZE)
    logger.info(f"데이터 샘플링: {DATA_SAMPLE_SIZE}개 업로드 시작...")
    
    # --- 2. DB에 삽입 ---
    cursor = connection.cursor()
    insert_count = 0
    
    # (참고) INSERT IGNORE: id가 중복되어도 에러 없이 무시하고 넘어감
    sql = f"""
        INSERT IGNORE INTO products (id, product_name, description, image_file)
        VALUES (%s, %s, %s, %s)
    """
    
    for index, row in df_sample.iterrows():
        try:
            # (중요) CSV 컬럼명에 맞게 데이터를 가져옴
            product_id = str(row[ID_COLUMN]) # ID는 문자열로 통일
            product_name = str(row[NAME_COLUMN])
            description = str(row[DESC_COLUMN])
            image_file = str(row[IMAGE_COLUMN])
            
            cursor.execute(sql, (product_id, product_name, description, image_file))
            insert_count += 1
            
        except KeyError:
            logger.warning(f"경고: CSV에 필요한 컬럼(예: '{ID_COLUMN}')이 없습니다. 건너뜁니다.")
        except Exception as e:
            logger.warning(f"경고: 데이터 삽입 중 에러 ({e}), 건너뜁니다. (데이터: {row})")

    # --- 3. 변경사항 저장 및 종료 ---
    try:
        connection.commit()
        logger.info("="*30)
        logger.info(f"🎉 성공! 총 {insert_count}개의 제품 정보를 DB에 업로드했습니다.")
        logger.info("="*30)
    except pymysql.MySQLError as e:
        logger.error(f"❌ DB 커밋 실패: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# --- 4. 스크립트 실행 ---
if __name__ == "__main__":
    
    # (중요!) backend/.env 파일 세팅 확인
    if DB_PASSWORD == "your_password" or DB_PASSWORD is None:
        logger.error("="*30)
        logger.error("❌ 에러: DB_PASSWORD가 설정되지 않았습니다!")
        logger.error("backend/.env 파일에 DB_PASSWORD=... 를 추가해주세요.")
        logger.error("="*30)
    else:
        conn = connect_db()
        if conn:
            upload_data(conn)