import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# 환경변수 로드
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

# MySQL 연결 URL (PyMySQL 사용)
DB_URL = f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}/{os.getenv('DB_NAME', 'lmm_project')}"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 의존성 주입용 함수 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()