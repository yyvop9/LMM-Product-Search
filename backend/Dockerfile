# 1. Conda 환경을 기반으로 시작
FROM continuumio/miniconda3

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. environment.yml 복사
COPY environment.yml .

# 4. Conda 환경 생성
RUN conda env create -f environment.yml

# (!!!) [핵심 수정] 환경변수 PATH 설정
# lmm-backend 환경의 bin 폴더를 시스템 경로(PATH)의 맨 앞에 추가함.
# 이제 'python', 'pip', 'uvicorn'을 치면 자동으로 가상환경의 것이 실행됨.
ENV PATH /opt/conda/envs/lmm-backend/bin:$PATH

# 5. 소스 코드 복사
COPY . .

# 6. 포트 개방
EXPOSE 8000

# 7. 실행 명령
# PATH를 설정했으므로 'conda run' 없이 바로 uvicorn 실행 가능
# (docker-compose.yml의 command가 이 줄을 덮어쓰지만, 기본값으로 둠)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]