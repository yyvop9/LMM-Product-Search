import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 모듈 임포트 (wishlist 라우터 추가!)
from .routers import auth, products, wishlist
from .database import engine, Base

# --- 1. 설정 및 로깅 초기화 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. 수명 주기 관리 (Lifespan Events) ---
# 서버가 시작될 때 무거운 AI 모델을 미리 로드합니다.
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 서버 시작 중... AI 모델 및 벡터 DB 로딩을 시작합니다.")
    
    # (중요) products 모듈에 있는 AI 로드 함수 실행
    products.load_ai_models()
    
    yield # 애플리케이션 실행 (Waiting for requests...)
    
    logger.info("🛑 서버 종료 중... 리소스를 정리합니다.")

# --- 3. 앱 초기화 ---
# DB 테이블 자동 생성 (users, products, wishlists 테이블이 없으면 생성)
Base.metadata.create_all(bind=engine)

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="Modify AI Search Engine",
    version="2.1.0",
    lifespan=lifespan
)

# --- 4. 미들웨어 설정 (CORS) ---
# 프론트엔드(React)와의 통신 허용
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*" # 개발 단계 편의상 전체 허용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. 정적 파일 서빙 (이미지) ---
# 경로 계산: backend/app/main.py -> (3단계 위) -> data/images
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "images"

# 이미지가 저장될 폴더가 없으면 자동 생성
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# URL 예시: http://localhost:8000/static/images/파일명.jpg
app.mount("/static/images", StaticFiles(directory=str(IMAGE_DIR)), name="static_images")

# --- 6. 라우터 등록 ---
# 각 기능별로 쪼개진 라우터를 메인 앱에 연결
app.include_router(auth.router)      # 회원가입, 로그인
app.include_router(products.router)  # 상품 검색, 등록, AI
app.include_router(wishlist.router)  # (!!!) 찜하기 기능 추가

# --- 7. 기본 엔드포인트 (Health Check) ---
@app.get("/")
def read_root():
    return {"message": "Modify AI Search Backend System is Ready (v2.1)"}

# --- 8. 서버 실행 (로컬 디버깅용) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)