import pandas as pd
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch
import pickle  # 파이썬 객체를 파일로 저장하는 라이브러리
from tqdm import tqdm  # 반복문 진행률을 시각적으로 보여주는 라이브러리
from pathlib import Path # 파일/폴더 경로를 쉽게 다루기 위한 라이브러리
import logging

# --- 0. 로깅 및 경로 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 이 스크립트 파일(create_embeddings.py)의 위치를 기준으로 경로 설정
SCRIPT_DIR = Path(__file__).parent # model/scripts/
PROJECT_ROOT = SCRIPT_DIR.parent.parent # LMM-Product-Search/
DATA_DIR = PROJECT_ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"

# (!!!) 여기 파일 이름을 실제 파일 이름으로 바꿔주세요 (예: data.csv)
CSV_PATH = DATA_DIR / "products.csv" 

OUTPUT_PATH = DATA_DIR / "product_vectors.pkl" # 최종 결과물 저장 위치

# 사용할 모델 ID
MODEL_ID = "openai/clip-vit-base-patch32"
# 처리할 데이터 개수 (테스트용)
DATA_SAMPLE_SIZE = 500


def load_model():
    """CLIP 모델과 프로세서를 로드합니다."""
    logger.info(f"'{MODEL_ID}' 모델 로드를 시작합니다...")
    
    # GPU 사용 가능 여부 확인 (있으면 훨씬 빠름)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"사용할 디바이스: {device}")

    try:
        # (중요) 노트북에서 성공했던 safetensors=True 옵션 사용
        model = CLIPModel.from_pretrained(MODEL_ID, use_safetensors=True).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_ID, use_safetensors=True)
        logger.info("✅ 모델 로드 성공!")
        return model, processor, device
    except Exception as e:
        logger.error(f"❌ 모델 로드 실패: {e}")
        return None, None, None


def process_images(model, processor, device):
    """CSV를 읽고, 이미지를 벡터로 변환하여 리스트로 반환합니다."""
    
    # --- [DEBUG] 경로 확인 코드 추가 ---
    print(f"\n--- [DEBUG] CSV 파일 경로: {CSV_PATH}")
    print(f"--- [DEBUG] CSV 파일 절대 경로: {CSV_PATH.resolve()}")
    print(f"--- [DEBUG] CSV 파일 존재 여부: {CSV_PATH.exists()}")
    # --- [DEBUG] ---

    try:
        df = pd.read_csv(CSV_PATH)
        logger.info(f"'{CSV_PATH}' 파일 로드 성공. (총 {len(df)}개 데이터)")
    except FileNotFoundError:
        logger.error(f"❌ 에러: '{CSV_PATH}' 파일을 찾을 수 없습니다.")
        return []

    # (중요) 테스트를 위해 500개만 샘플링
    df_sample = df.head(DATA_SAMPLE_SIZE)
    logger.info(f"데이터 샘플링: {DATA_SAMPLE_SIZE}개 처리 시작...")

    embeddings_list = [] # 결과를 저장할 리스트

    # tqdm을 사용하여 반복문 진행 상태 표시
    for index, row in tqdm(df_sample.iterrows(), total=df_sample.shape[0], desc="이미지 처리 중"):
        
        # (!!!) CSV의 'image' 컬럼명을 실제 파일과 맞게 수정하세요 (예: 'id' 또는 'image_file')
        image_filename = row['image'] 
        image_path = IMAGE_DIR / image_filename
        
        # 'id'는 파일명을 그대로 사용 (예: '1620.jpg')
        product_id = image_filename

        try:
            # 1. 이미지 열기
            image = Image.open(image_path)
            
            # 2. 이미지 처리 (프로세서)
            inputs = processor(images=image, return_tensors="pt", padding=True).to(device)
            
            # 3. 벡터 추출 (모델)
            with torch.no_grad(): # 추론 모드(속도 향상, 메모리 절약)
                image_vector = model.get_image_features(**inputs)
            
            # [1, 512] -> [512] 차원으로 변경하고, CPU로 이동, numpy 배열로 변환
            vector_np = image_vector.squeeze().cpu().numpy()
            
            # 4. 결과 저장
            embeddings_list.append({
                'id': product_id,
                'vector': vector_np
            })

        except FileNotFoundError:
            logger.warning(f"경고: '{image_path}' 이미지를 찾을 수 없어 건너뜁니다.")
        except Exception as e:
            logger.warning(f"경고: '{product_id}' 처리 중 에러 ({e}), 건너뜁니다.")
            
    return embeddings_list


def save_embeddings(embeddings_list):
    """변환된 벡터 리스트를 .pkl 파일로 저장합니다."""
    
    if not embeddings_list:
        logger.error("❌ 저장할 임베딩 데이터가 없습니다. 스크립트를 종료합니다.")
        return
        
    try:
        with open(OUTPUT_PATH, 'wb') as f:
            # pickle을 사용하여 리스트 객체를 바이너리 파일로 저장
            pickle.dump(embeddings_list, f)
        
        logger.info("="*30)
        logger.info(f"🎉 성공! 총 {len(embeddings_list)}개의 벡터를")
        logger.info(f"'{OUTPUT_PATH}' 파일에 저장했습니다.")
        logger.info("="*30)
        
    except Exception as e:
        logger.error(f"❌ 파일 저장 실패: {e}")


# --- 5. 스크립트 실행 ---
if __name__ == "__main__":
    model, processor, device = load_model()
    
    if model and processor:
        embeddings = process_images(model, processor, device)
        save_embeddings(embeddings)