# C:/LMM-Product-Search/frontend/Dockerfile

# 1. Node.js 18 버전을 기반으로 시작
FROM node:20-alpine

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. package.json과 package-lock.json(또는 yarn.lock) 복사
COPY package*.json ./

# 4. 의존성 설치 (Vite 프로젝트이므로 npm install)
RUN npm install

# 5. 프론트엔드의 나머지 모든 소스 코드 복사
COPY . .

# 6. Vite 개발 서버 포트 5173번 개방
EXPOSE 5173

# 7. (중요!) 개발 서버 실행
# "--host" 옵션: 컨테이너 외부(호스트 PC)에서도 접속 가능하게 함
CMD ["npm", "run", "dev", "--", "--host"]