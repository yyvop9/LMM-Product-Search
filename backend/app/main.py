import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# 모듈 임포트
try:
    from app.routers import auth, products, wishlist
    from app.database import engine, Base
except ImportError:
    from .routers import auth, products, wishlist
    from .database import engine, Base

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# [핵심 경로 수정] Docker 환경에 맞춰 절대 경로 사용
# Dockerfile의 WORKDIR가 /app 이므로 데이터는 /app/data
IMAGE_DIR = Path("/app/data/images")

if not IMAGE_DIR.exists():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 이미지 폴더 생성: {IMAGE_DIR}")
else:
    logger.info(f"📂 이미지 폴더 확인: {IMAGE_DIR}")

# 수명 주기 (AI 모델 로드)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 [System] 서버 시작... AI 모델 로딩 시도...")
    Base.metadata.create_all(bind=engine)
    
    try:
        # products.py의 전역변수 ml_models를 채우는 함수 호출
        products.load_ai_models()
        logger.info("✅ [AI] 모델 로드 로직 실행 완료.")
    except Exception as e:
        logger.error(f"❌ [AI] 모델 로드 중 에러 발생: {e}")

    yield
    logger.info("🛑 [System] 서버 종료.")

# 앱 초기화
app = FastAPI(
    title="Modify AI Search",
    version="2.2.0",
    lifespan=lifespan
)

# CORS 설정
origins = ["*"] # 개발용 전체 허용

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static/images", StaticFiles(directory=str(IMAGE_DIR)), name="static_images")

# 글로벌 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 [Server Error] {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )

# 라우터 등록
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(wishlist.router)

@app.get("/")
def read_root():
    return {"status": "online", "image_dir": str(IMAGE_DIR)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)