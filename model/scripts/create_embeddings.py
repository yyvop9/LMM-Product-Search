import pandas as pd
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch
import pickle
from tqdm import tqdm
from pathlib import Path
import logging

# --- 0. 로깅 및 경로 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent # LMM-Product-Search/
DATA_DIR = PROJECT_ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"
CSV_PATH = DATA_DIR / "products.csv"
OUTPUT_PATH = DATA_DIR / "product_vectors.pkl"

# 모델 및 데이터 설정
MODEL_ID = "openai/clip-vit-base-patch32"
DATA_SAMPLE_SIZE = 5000 # (원하는 데이터 개수만큼 설정)

def load_model():
    """CLIP 모델과 프로세서를 로드합니다."""
    logger.info(f"'{MODEL_ID}' 모델 로드 중...")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"사용할 디바이스: {device}")

    try:
        model = CLIPModel.from_pretrained(MODEL_ID, use_safetensors=True).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_ID, use_safetensors=True)
        return model, processor, device
    except Exception as e:
        logger.error(f"❌ 모델 로드 실패: {e}")
        return None, None, None

def process_images(model, processor, device):
    """이미지를 벡터로 변환합니다 (한글 인코딩 처리 포함)."""
    
    # 1. CSV 파일 읽기 (한글 깨짐 방지)
    try:
        try:
            # 먼저 utf-8-sig (CSV 표준) 시도
            df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
        except UnicodeDecodeError:
            # 실패 시 cp949 (윈도우 엑셀 저장 방식) 시도
            logger.warning("UTF-8 읽기 실패. CP949로 다시 시도합니다...")
            df = pd.read_csv(CSV_PATH, encoding='cp949')
            
        logger.info(f"'{CSV_PATH}' 로드 성공. (총 {len(df)}개)")
        
        # [디버깅] 첫 번째 파일명이 한글로 잘 나오는지 확인
        if not df.empty:
            print(f"--- [DEBUG] 첫 번째 파일명 확인: {df.iloc[0]['image_filename']}")
            
    except FileNotFoundError:
        logger.error(f"❌ 파일 없음: {CSV_PATH}")
        return []
    except Exception as e:
        logger.error(f"❌ CSV 읽기 실패: {e}")
        return []

    # 2. 데이터 샘플링
    df_sample = df.head(DATA_SAMPLE_SIZE)
    embeddings_list = []

    # 3. 벡터 변환 루프
    for index, row in tqdm(df_sample.iterrows(), total=len(df_sample), desc="벡터 변환 중"):
        try:
            # (주의) CSV 컬럼명이 'image_filename'인지 확인하세요
            image_filename = row['image_filename'] 
            image_path = IMAGE_DIR / image_filename
            
            # 이미지 열기
            image = Image.open(image_path)
            
            # 모델 입력 생성
            inputs = processor(images=image, return_tensors="pt", padding=True).to(device)
            
            # 벡터 추출
            with torch.no_grad():
                image_vector = model.get_image_features(**inputs)
            
            # Numpy 변환 및 저장
            vector_np = image_vector.squeeze().cpu().numpy()
            
            embeddings_list.append({
                'id': image_filename,
                'vector': vector_np
            })

        except FileNotFoundError:
            # 이미지가 없는 경우 조용히 넘어감 (또는 경고 로그)
            # logger.warning(f"이미지 없음: {image_filename}")
            pass 
        except Exception as e:
            logger.warning(f"에러 ({image_filename}): {e}")
            
    return embeddings_list

def save_embeddings(embeddings_list):
    """결과를 .pkl 파일로 저장합니다."""
    if not embeddings_list:
        logger.error("❌ 저장할 벡터가 없습니다. (모든 이미지 변환 실패)")
        return
        
    try:
        with open(OUTPUT_PATH, 'wb') as f:
            pickle.dump(embeddings_list, f)
        
        logger.info("="*30)
        logger.info(f"🎉 성공! {len(embeddings_list)}개의 벡터를 저장했습니다.")
        logger.info(f"파일 위치: {OUTPUT_PATH}")
        logger.info("="*30)
    except Exception as e:
        logger.error(f"❌ 파일 저장 실패: {e}")

# --- 실행 ---
if __name__ == "__main__":
    model, processor, device = load_model()
    
    if model:
        embeddings = process_images(model, processor, device)
        save_embeddings(embeddings)