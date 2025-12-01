# 1. Conda 환경을 기반으로 시작
FROM continuumio/miniconda3

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. environment.yml 복사
COPY environment.yml .

# 4. Conda 환경 생성 (네트워크 강화 버전)
# - remote_read_timeout_secs: 다운로드 대기 시간을 10분으로 연장
# - || : 앞의 명령어가 실패하면 뒤의 명령어(재시도)를 실행
RUN conda config --set remote_read_timeout_secs 600 && \
    (conda env create -f environment.yml || \
     (echo "⚠️ 1차 다운로드 실패. 5초 후 재시도합니다..." && sleep 5 && conda env create -f environment.yml)) && \
    conda clean -afy

# (!!!) [핵심 수정] 환경변수 PATH 설정
# lmm-backend 환경의 bin 폴더를 시스템 경로(PATH)의 맨 앞에 추가함.
ENV PATH /opt/conda/envs/lmm-backend/bin:$PATH

# 5. 소스 코드 복사
COPY . .

# 6. 포트 개방
EXPOSE 8000

# 7. 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]