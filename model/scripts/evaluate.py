import requests # API를 호출하기 위한 라이브러리
import logging
from pathlib import Path
import pandas as pd

# --- 0. 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 1. (!!!) 우리가 직접 만들 '정답지' (Test Set) ---
# (이건 예시입니다. data/products.csv를 보고 본인 데이터에 맞게 수정해야 합니다!)
TEST_SET = [
    {
        "query": "파란색 셔츠",
        "expected_ids": ["9378.jpg", "58879.jpg", "23122.jpg"] # (예시 ID)
    },
    {
        "query": "바지",
        "expected_ids": ["10005.jpg", "30588.jpg"] # (예시 ID)
    },
    {
        "query": "빨간색 드레스",
        "expected_ids": ["1644.jpg"] # (예시 ID)
    },
    # (여기에 테스트 케이스를 10~20개 정도 직접 추가해야 합니다)
]

# --- 2. API 설정 ---
API_URL = "http://localhost:8000/search/text"
K = 5 # 상위 5개(K=5)의 정밀도를 측정

def evaluate_precision():
    """
    TEST_SET을 기반으로 Precision@K를 계산합니다.
    (!!!) 이 스크립트를 실행하기 전에, docker-compose up이 켜져 있어야 합니다!
    """
    
    total_precision = 0.0
    total_queries = len(TEST_SET)
    
    if total_queries == 0:
        logger.error("❌ 테스트셋(TEST_SET)이 비어있습니다. 스크립트를 수정해주세요.")
        return

    logger.info(f"--- 총 {total_queries}개의 쿼리로 Precision@{K} 평가를 시작합니다. ---")

    for test_case in TEST_SET:
        query = test_case["query"]
        expected_ids = set(test_case["expected_ids"]) # 비교를 위해 set으로 변환
        
        try:
            # 1. FastAPI 백엔드 API 호출
            response = requests.post(API_URL, json={"query": query, "top_k": K})
            
            if response.status_code != 200:
                logger.warning(f"쿼리 '{query}' 실패: {response.status_code} {response.text}")
                continue

            results = response.json() # 결과 (list of dict)
            
            # 2. 결과에서 ID만 추출
            # (결과가 비어있을 수 있으므로 .get() 사용)
            recommended_ids = set([item.get("id") for item in results])
            
            # 3. 정답과 추천 목록 비교
            correct_hits = recommended_ids.intersection(expected_ids)
            
            # 4. Precision@K 계산
            if K > 0:
                precision_at_k = len(correct_hits) / K
            else:
                precision_at_k = 0.0
                
            logger.info(f"  [쿼리: '{query}']")
            logger.info(f"    - 추천(AI): {recommended_ids}")
            logger.info(f"    - 정답(인간): {expected_ids}")
            logger.info(f"    - 정답 수: {len(correct_hits)} / {K}개")
            logger.info(f"    - P@{K} 점수: {precision_at_k:.2%}")
            
            total_precision += precision_at_k

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ API 서버({API_URL})에 연결할 수 없습니다.")
            logger.error("    (!!!) 'docker-compose up'이 실행 중인지 확인하세요!")
            return
        except Exception as e:
            logger.error(f"쿼리 '{query}' 처리 중 예외 발생: {e}")

    # --- 5. 최종 평균 점수 ---
    average_precision = total_precision / total_queries
    
    logger.info("="*40)
    logger.info(f"📊 최종 평가 완료")
    logger.info(f"  총 평균 Precision@{K}: {average_precision:.2%}")
    logger.info("="*40)

# --- 6. 스크립트 실행 ---
if __name__ == "__main__":
    # (API 호출을 위해 requests 라이브러리가 필요함)
    # (lmm-model 환경에 설치)
    # conda activate lmm-model
    # pip install requests
    
    evaluate_precision()