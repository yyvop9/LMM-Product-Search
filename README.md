Modify (LMM AI 제품 검색 시스템)
Modify는 **LMM(Large Multimodal Model)**과 **LLM(Large Language Model)**을 활용한 지능형 패션 커머스 검색 엔진입니다. 사용자의 텍스트/이미지 검색 의도를 파악하여, 시각적 유사도가 높은 제품을 추천합니다.

✨ 주요 기능
텍스트 검색: "파란색 셔츠"와 같은 키워드로 스타일 검색 (CLIP 기반)

이미지 검색: 사용자가 업로드한 이미지와 유사한 스타일의 제품 추천

스마트 검색 (AI Agent): "오늘 크리스마스인데 뭘 입어?" 같은 자연어 질문을 이해하고 추천 (IBM Watsonx / OpenAI 연동)

연관 상품 추천: 상품 클릭 시 유사한 스타일의 다른 상품 추천

관리자 로그: 사용자 검색 기록 자동 저장 및 관리자 대시보드 제공

🛠️ 기술 스택 (Tech Stack)
Frontend: React, Vite

Backend: FastAPI, Python 3.10

AI Core: PyTorch, OpenAI CLIP, IBM Watsonx.ai

Database: MySQL 8.0

Infrastructure: Docker, Docker Compose

🚀 설치 및 실행 가이드 (Getting Started)
이 프로젝트를 로컬 환경에서 실행하기 위한 단계입니다.

1. 필수 요구 사항 (Prerequisites)
Git 설치

Docker Desktop 설치 및 실행 (필수!)

(선택) Anaconda (로컬 데이터 전처리용)

2. 프로젝트 클론 (Clone)
Bash

git clone https://github.com/[본인아이디]/LMM-Product-Search.git
cd LMM-Product-Search
3. 데이터 파일 준비 (중요! ⚠️)
이 저장소에는 대용량 데이터 파일이 포함되어 있지 않습니다. data/ 폴더를 프로젝트 루트에 생성하고, 아래 파일들을 넣어주세요.

Plaintext

LMM-Product-Search/
└── data/
    ├── images/               # (폴더) 제품 이미지 파일들 (.jpg)
    ├── products.csv          # (파일) 제품 정보 CSV
    └── product_vectors.pkl   # (파일) AI 벡터 데이터 (없으면 아래 스크립트로 생성)
(※ product_vectors.pkl이 없다면, conda 환경에서 model/scripts/create_embeddings.py를 실행하여 생성해야 합니다.)

1. 필수 요구 사항 (Prerequisites)
Git 설치

Docker Desktop 설치 및 실행 (필수!)

(선택) Anaconda (로컬 데이터 전처리용)

2. 프로젝트 클론 (Clone)
Bash

git clone https://github.com/[본인아이디]/LMM-Product-Search.git
cd LMM-Product-Search
3. 데이터 파일 준비 (중요! ⚠️)
이 저장소에는 대용량 데이터 파일이 포함되어 있지 않습니다. data/ 폴더를 프로젝트 루트에 생성하고, 아래 파일들을 넣어주세요.

Plaintext

LMM-Product-Search/
└── data/
    ├── images/               # (폴더) 제품 이미지 파일들 (.jpg)
    ├── products.csv          # (파일) 제품 정보 CSV
    └── product_vectors.pkl   # (파일) AI 벡터 데이터 (없으면 아래 스크립트로 생성)
(※ product_vectors.pkl이 없다면, conda 환경에서 model/scripts/create_embeddings.py를 실행하여 생성해야 합니다.)

4. 환경 변수 설정 (.env)
각 폴더에 .env 파일을 생성해야 합니다. (.env.example 참고)

1) 백엔드 설정 (backend/.env)

코드 스니펫


# DB 설정
DB_HOST=db
DB_USER=root
DB_PASSWORD=12345
DB_NAME=lmm_project

# IBM Watsonx 설정 (스마트 검색용)
WATSONX_API_KEY=여기에_API_키_입력
WATSONX_PROJECT_ID=여기에_프로젝트_ID_입력
WATSONX_URL=https://us-south.ml.cloud.ibm.com
2) 프론트엔드 설정 (frontend/.env)

코드 스니펫

VITE_API_BASE_URL=http://localhost:8000
5. Docker 실행 (서비스 시작)
프로젝트 루트 폴더에서 아래 명령어를 실행합니다.

Bash
# 이미지 빌드 및 컨테이너 실행
docker-compose up --build
최초 실행 시 이미지를 다운로드하고 빌드하는 데 10분 이상 소요될 수 있습니다.

frontend-1, backend-1, db-1 컨테이너가 모두 정상적으로 켜졌는지 확인하세요.

💾 데이터베이스 초기화 (최초 1회)
Docker가 실행 중인 상태에서, 새 터미널을 열고 아래 명령어를 순서대로 실행하여 DB를 세팅합니다.

1. 테이블 생성
Bash

# 1. DB 접속
docker-compose exec db mysql -u root -p12345 lmm_project
MySQL 접속 후 아래 SQL 실행:

SQL

-- 제품 테이블
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

-- 로그 테이블
CREATE TABLE IF NOT EXISTS search_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    search_type VARCHAR(10) NOT NULL,
    query VARCHAR(255) NULL,
    filename VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 종료
exit
2. 데이터 업로드
Bash

# backend 컨테이너 내부에서 업로드 스크립트 실행
docker-compose exec backend conda run -n lmm-backend python scripts/upload_to_mysql.py
"🎉 성공! 총 N개의 데이터를 업로드했습니다." 메시지가 뜨면 완료입니다.

🖥️ 사용 방법 (Usage)
웹 서비스 접속 (Frontend): http://localhost:5173

API 문서 (Swagger UI): http://localhost:8000/docs

주요 기능 테스트
텍스트 검색: 검색창에 "겨울 코트", "청바지" 등을 입력.

이미지 검색: 가지고 있는 의류 이미지를 업로드.

스마트 검색: "이번 주말 데이트하는데 입을 옷 추천해줘" (Watsonx 연동 필요).

상세/연관: 검색 결과 이미지를 클릭하여 상세 페이지 및 연관 상품 확인.

❗ 트러블슈팅 (FAQ)
Q. Error response from daemon: open ... dockerDesktopLinuxEngine ... 에러가 떠요. A. Docker Desktop 프로그램이 실행되지 않았습니다. Docker를 먼저 실행해 주세요.

Q. Failed to resolve import "react-router-dom" 에러가 떠요. A. 로컬의 node_modules와 충돌이 발생한 것입니다.

docker-compose down으로 종료.

frontend/node_modules 폴더 삭제.

docker-compose up --build 다시 실행.

Q. 검색 결과가 이상하거나 안 나와요. A. data/product_vectors.pkl 파일이 data/products.csv와 일치하는지 확인하세요. 데이터가 변경되었다면 벡터를 재생성하고 서버를 재시작해야 합니다.