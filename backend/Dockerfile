# C:/LMM-Product-Search/backend/Dockerfile

# 1. Conda 환경을 기반으로 시작
FROM continuumio/miniconda3

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. (중요!) environment.yml 파일을 먼저 복사
COPY environment.yml .

# 4. (중요!) yml 파일로 lmm-backend 환경 생성
# (시간이 꽤 걸릴 수 있습니다)
RUN conda env create -f environment.yml

# 5. Conda 환경을 기본 쉘로 설정
SHELL ["conda", "run", "-n", "lmm-backend", "/bin/bash", "-c"]

# 6. 백엔드의 나머지 모든 소스 코드 복사
COPY . .

# 7. 서버 포트 8000번 개방
EXPOSE 8000

# 8. (중요!) lmm-backend 환경에서 FastAPI 서버 실행
# uvicorn app.main:app --host 0.0.0.0 --port 8000
CMD ["conda", "run", "-n", "lmm-backend", "python", "app/main.py"]