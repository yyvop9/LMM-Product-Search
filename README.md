🛍️ Modify (LMM AI Product Search Engine)

Modify는 LMM(Large Multimodal Model)인 CLIP과 LLM인 IBM Watsonx를 결합한 차세대 패션 검색 엔진입니다.
단순 키워드 매칭을 넘어, 사용자의 의도(Context)와 시각적 스타일(Visual Style)을 이해하여 제품을 추천합니다.

(여기에 나중에 아키텍처 다이어그램 이미지를 넣으면 좋습니다)

✨ Key Features (핵심 기능)

텍스트 검색 (Text Search): "파란색 셔츠" 등 키워드로 스타일 검색 (CLIP 기반 + 한영 번역기)

이미지 검색 (Image Search): 가지고 있는 옷 사진을 업로드하여 유사한 스타일 찾기

스마트 검색 (AI Agent): "크리스마스 데이트룩 추천해줘" 같은 자연어 질문 이해 (IBM Watsonx + Prompt Engineering)

연관 상품 추천: 상품 클릭 시 시각적으로 유사한 다른 상품 추천

하이브리드 필터링: AI 벡터 검색 + DB 메타데이터(계절, 성별 등) 필터링 결합

🛠️ Tech Stack (기술 스택)

Frontend: React (Vite), CSS Modules

Backend: FastAPI (Python 3.10)

AI Core: PyTorch, OpenAI CLIP, IBM Watsonx.ai (Llama 3)

Database: MySQL 8.0 (Metadata), Pickle (Vector Index)

DevOps: Docker, Docker Compose

🚀 Installation & Setup (설치 및 실행)

이 프로젝트를 로컬 환경에서 실행하기 위한 가이드입니다.

1. Prerequisites (사전 준비)

Git 설치

Docker Desktop 설치 및 실행 (필수)

(선택) Anaconda (로컬 데이터 전처리 시 필요)

2. Clone Repository

git clone [https://github.com/](https://github.com/)[YOUR_GITHUB_ID]/LMM-Product-Search.git
cd LMM-Product-Search


3. Data Setup (⚠️ 중요)

이 저장소에는 대용량 이미지와 데이터 파일이 포함되어 있지 않습니다.
data/ 폴더를 프로젝트 루트에 직접 생성하고, 원본 데이터를 위치시켜야 합니다.

LMM-Product-Search/
└── data/
    ├── images/               # (폴더) 제품 이미지 파일들 (.jpg)
    ├── products.csv          # (파일) 제품 정보 CSV
    └── product_vectors.pkl   # (파일) AI 벡터 데이터


(※ product_vectors.pkl이 없다면 model/scripts/create_embeddings.py를 실행하여 생성해야 합니다.)

4. Environment Variables (.env)

각 폴더에 .env 파일을 생성하고 설정을 입력하세요. (.env.example 참고)

backend/.env

DB_HOST=db
DB_USER=root
DB_PASSWORD=12345
DB_NAME=lmm_project

# IBM Watsonx (스마트 검색용)
WATSONX_API_KEY=your_ibm_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=[https://us-south.ml.cloud.ibm.com](https://us-south.ml.cloud.ibm.com)


frontend/.env

VITE_API_BASE_URL=http://localhost:8000


5. Run with Docker (실행)

# 이미지 빌드 및 컨테이너 실행
docker-compose up --build


최초 실행 시 AI 모델 다운로드 등으로 인해 10분 이상 소요될 수 있습니다.

💾 Database Initialization (최초 1회)

서버가 켜진 상태에서, 새 터미널을 열고 DB를 세팅해야 합니다.

테이블 생성:

docker-compose exec db mysql -u root -p(본인db비번으로) lmm_project


MySQL 접속 후 아래 SQL 실행:

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(255) NOT NULL,
    product_name VARCHAR(255) NULL,
    description TEXT NULL,
    brand VARCHAR(100) NULL,
    color VARCHAR(100) NULL,
    size VARCHAR(100) NULL,
    price INT NULL,
    season VARCHAR(100) NULL,
    image_file VARCHAR(255) NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS search_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    search_type VARCHAR(10) NOT NULL,
    query VARCHAR(255) NULL,
    filename VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
exit


데이터 업로드:

docker-compose exec backend conda run -n lmm-backend python scripts/upload_to_mysql.py


🖥️ Usage (사용 방법)

브라우저 접속: http://localhost:5173

텍스트 검색: "겨울 코트" 입력 -> [검색]

AI 스마트 검색: "크리스마스 데이트룩 추천해줘" 입력 -> [✨ AI 추천]

이미지 검색: 파일 업로드 -> [이미지로 검색]

📊 Performance (성능 평가)

Accuracy: LLM 기반 쿼리 확장 및 필터링 도입으로 기존 키워드 검색 대비 정확도 3.5배 향상 (20% -> 75%)

Efficiency: 벡터 검색을 통해
