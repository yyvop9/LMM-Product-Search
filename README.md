# 🚀 P5: LMM 기반 AI 스타일 검색 및 추천 시스템

> 5명의 팀원이 진행하는 '핀터레스트 미니 버전' 파이널 프로젝트입니다.
> LMM(Large Multimodal Model)을 사용하여 이미지와 텍스트로 상품을 검색하고,
> 취향에 맞는 스타일을 AI가 추천하는 웹 서비스입니다.

## 👥 팀원 (Team PentaPixel)

| 역할 | 이름 | 담당 |
| :--- | :--- | :--- |
| 🛠️ **PM / DevOps** | (팀장님 성함) | 프로젝트 총괄, Git/Infra, 배포 |
| 🧠 **AI / Data** | (팀원 1) | LMM 모델링, 데이터 수집/전처리 |
| ⚙️ **Backend** | (팀원 2) | FastAPI API 서버 개발 |
| 💾 **DB / Data Eng.** | (팀원 3) | 벡터 DB 구축, 데이터 파이프라인 |
| 🎨 **Frontend** | (팀원 4) | React 웹 UI/UX 개발 |

<br>

## 📦 기술 스택 (Tech Stack)

* **AI**: `PyTorch`, `Transformers (CLIP)`, `Hugging Face`
* **Backend**: `FastAPI (Python)`, `Gunicorn`
* **Frontend**: `React (JavaScript)`, `Axios`
* **Database**: `PostgreSQL` (제품 정보용), `Milvus` (벡터 검색용)
* **DevOps**: `Docker`, `Docker-Compose`

<br>

## 🏃‍♀️ 실행 방법 (Getting Started)

> [!IMPORTANT]
> 자세한 개발 환경 세팅 방법은 `docs/setup.md` 문서를 참고하세요.

### 1. 저장소 클론
```bash
git clone https://(여러분의_저장소_주소).git
cd LMM-Product-Search