# 🛍️ Modify (LMM AI Fashion Search Engine)

**Modify**는 텍스트와 이미지를 동시에 이해하는 **LMM(Large Multimodal Model)** 기반의 차세대 패션 검색 엔진입니다.
단순 키워드 매칭을 넘어, **사용자의 의도(Context), 계절(Season), 가격대(Price)**를 AI가 스스로 추론하여 최적의 스타일을 제안합니다.

## 📊 System Architecture

```mermaid
graph TD
    User([👤 User]) --> FE[🖥️ Frontend (React)]
    FE --> BE[⚙️ Backend (FastAPI)]
    
    subgraph AI_Engine [🧠 AI Core]
        BE --> Watsonx[IBM Watsonx (Intent Analysis)]
        BE --> CLIP[OpenAI CLIP (Visual Embedding)]
    end
    
    subgraph Data_Layer [📦 Data Store]
        BE --> MySQL[(MySQL 8.0 - Meta)]
        BE --> VectorDB[(Pickle - Vector Index)]
    end
    
    DataScript[🛠️ Auto-Ingestion Script] --> MySQL
    DataScript --> VectorDB
✨ Key Features (핵심 기능)
AI 스마트 검색 (Smart Search):

"남자친구랑 데이트할 때 입을 옷" → (Gender: Women, Style: Date, Category: Onepiece/Skirt) 자동 변환.

"가성비 좋은 여름 니트" → (Price: ~50,000, Season: Summer, Material: Knit) 역설적 표현 이해.

하이브리드 필터링 (Hybrid Search):

DB 메타데이터 필터링 + Vector 이미지 유사도 검색을 결합하여 정확도 극대화.

검색 결과가 부족할 경우 자동으로 조건을 완화하여 유사 상품을 찾아내는 Fallback System 탑재.

이미지 검색 (Visual Search):

사용자가 업로드한 옷 사진을 분석하여 가장 비슷한 스타일의 상품 추천.

데이터 파이프라인 자동화:

CSV와 이미지 파일만 넣으면 카테고리/성별/계절 자동 태깅 및 DB/벡터 동기화가 한 번에 수행됨.

🛠️ Tech Stack
Frontend: React (Vite), Tailwind CSS, Framer Motion, Lucide React

Backend: FastAPI, SQLAlchemy, Pydantic

AI/ML: OpenAI CLIP (ViT-L/14), IBM Watsonx (Llama-3-70b)

Database: MySQL 8.0, FAISS/Pickle (Vector Store)

Infra: Docker, Docker Compose

🚀 Installation & Setup (설치 및 실행)
1. Prerequisites (사전 준비)
Git & Docker Desktop 설치 필수.

IBM Watsonx API Key (스마트 검색 기능 사용 시 필요).

2. Clone Repository
Bash

git clone [https://github.com/](https://github.com/)[YOUR_GITHUB_ID]/LMM-Product-Search.git
cd LMM-Product-Search
3. Data Setup (⚠️ 필수)
이 저장소는 대용량 데이터를 포함하지 않습니다. 프로젝트 루트에 data 폴더를 만들고 원본 데이터를 넣으세요.

Plaintext

LMM-Product-Search/
└── data/
    ├── images/           # (폴더) 제품 이미지 파일들 (.jpg, .png)
    ├── products.csv      # (파일) 제품 메타데이터 CSV
    └── product_vectors.pkl # (자동 생성됨, 초기엔 없어도 됨)
4. Environment Variables (.env)
각 폴더에 .env 파일을 생성하세요.

backend/.env

코드 스니펫

DB_HOST=db
DB_USER=root
DB_PASSWORD=12345
DB_NAME=lmm_project

# IBM Watsonx (Smart Search)
WATSONX_API_KEY=your_ibm_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=[https://us-south.ml.cloud.ibm.com](https://us-south.ml.cloud.ibm.com)
frontend/.env

코드 스니펫

VITE_API_URL=http://localhost:8000
5. Run with Docker (실행)
모든 서비스(Frontend, Backend, DB)를 한 번에 실행합니다.

Bash

docker-compose up -d --build
Note: 최초 실행 시 MySQL 초기화 및 AI 모델 다운로드로 인해 약 3~5분 소요될 수 있습니다.

💾 Data Initialization (데이터 구축)
복잡한 SQL 명령어 없이, 스크립트 하나로 해결됩니다. 아래 파이썬 스크립트를 실행하면 **[DB 초기화 + CSV 데이터 로드 + AI 벡터 생성]**이 자동으로 수행됩니다.

Bash

# 1. 데이터 구축 스크립트 실행 (도커 내부에서 실행됨)
docker exec -it lmm-backend python scripts/import_csv_data.py
기능: 기존 데이터를 안전하게 삭제하고, CSV와 이미지를 읽어 DB와 벡터 파일을 완벽하게 동기화합니다.

소요 시간: 이미지 2,000장 기준 약 10~15분 (CPU 모드).

작업이 완료되면(🎉 작업 완료! 메시지), 서버를 재시작하여 데이터를 반영하세요.

Bash

docker restart lmm-backend
🖥️ Usage (사용 방법)
웹사이트 접속: http://localhost:5173

로그인: (DB 초기화 시 계정이 없다면 회원가입 진행)

검색 테스트:

"여름에 입기 좋은 시원한 남자 셔츠"

"가성비 좋은 검정 패딩"

"여자친구랑 데이트할 때 입을 옷"

⚠️ Troubleshooting
Q. 검색 결과가 0개입니다.

A. import_csv_data.py를 실행했는지 확인하세요. 실행 후 **반드시 docker restart lmm-backend**를 해야 서버가 벡터 데이터를 로드합니다.

Q. 이미지가 엑박(Broken Image)으로 뜹니다.

A. data/images 폴더에 실제 이미지 파일이 있는지 확인하세요. 파일명이 한글일 경우 CSV와 정확히 일치해야 합니다.

Q. 로그인 시 422 에러가 뜹니다.

A. 최신 코드가 적용되었는지 확인하세요. (git pull 또는 frontend/src/pages/LoginPage.jsx 확인)