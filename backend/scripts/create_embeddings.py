import pandas as pd
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch
import pickle
from tqdm import tqdm
from pathlib import Path
import logging
import sys
import os

# --- 0. 로깅 및 경로 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 경로 설정 (백엔드 구조에 맞게 조정)
# 현재 파일 위치: backend/scripts/create_embeddings.py
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent 
DATA_DIR = PROJECT_ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"
CSV_PATH = DATA_DIR / "products.csv"
OUTPUT_PATH = DATA_DIR / "product_vectors.pkl"

# --- [Configuration] 모델 업그레이드 ---
# (기존) "openai/clip-vit-base-patch32" -> 512차원
# (변경) "openai/clip-vit-large-patch14" -> 768차원 (정확도 대폭 상승)
MODEL_ID = "openai/clip-vit-large-patch14" 
DATA_SAMPLE_SIZE = 5000 

def load_model():
    """CLIP 모델 로드 (GPU 가속 권장)"""
    logger.info(f"🚀 모델 로드 중: '{MODEL_ID}'")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"🖥️  사용 Device: {device}")

    try:
        # safetensors=True는 최신 모델 로딩 표준 (보안/속도)
        model = CLIPModel.from_pretrained(MODEL_ID, use_safetensors=True).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_ID, use_safetensors=True)
        return model, processor, device
    except Exception as e:
        logger.error(f"❌ 모델 로드 실패. 인터넷 연결이나 패키지 버전을 확인하세요.\n에러: {e}")
        return None, None, None

def process_images(model, processor, device):
    """이미지를 벡터로 변환 (배치 처리 없음 - 단순 루프)"""
    
    if not CSV_PATH.exists():
        logger.error(f"❌ CSV 파일 없음: {CSV_PATH}")
        return []

    # 1. CSV 읽기 (인코딩 호환성)
    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_PATH, encoding='cp949')
    
    # 데이터 샘플링
    df = df.head(DATA_SAMPLE_SIZE)
    logger.info(f"📂 데이터 {len(df)}개 처리 시작...")

    embeddings_list = []
    success_count = 0

    # 2. 벡터 변환
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Embedding"):
        try:
            # 컬럼명 방어 로직 (image_filename 또는 filename)
            fname = row.get('image_filename') or row.get('filename')
            if not fname: continue

            image_path = IMAGE_DIR / str(fname)
            
            # 이미지 로드 및 전처리
            image = Image.open(image_path).convert("RGB") # RGB 변환 중요 (PNG 투명도 이슈 방지)
            
            # 모델 추론
            inputs = processor(images=image, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                # [Large 모델] 출력 차원: 768
                image_features = model.get_image_features(**inputs)
                
                # 정규화 (Cosine Similarity 정확도 향상)
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            
            # Numpy 변환
            vector_np = image_features.squeeze().cpu().numpy()
            
            # 결과 저장 (ID는 추후 검색 매핑용)
            # CSV에 id 컬럼이 있으면 쓰고, 없으면 파일명을 ID로 사용
            item_id = str(row.get('id', fname))
            
            embeddings_list.append({
                'id': item_id,
                'vector': vector_np
            })
            success_count += 1

        except FileNotFoundError:
            pass # 이미지 없으면 스킵
        except Exception as e:
            # logger.warning(f"Skipped {fname}: {e}")
            pass

    logger.info(f"✨ 변환 완료: {success_count}/{len(df)} 성공")
    return embeddings_list

def save_embeddings(embeddings_list):
    """벡터 데이터를 pkl 파일로 덤프"""
    if not embeddings_list:
        logger.error("❌ 저장할 데이터가 없습니다.")
        return

    try:
        with open(OUTPUT_PATH, 'wb') as f:
            pickle.dump(embeddings_list, f)
        logger.info(f"💾 저장 완료: {OUTPUT_PATH}")
        logger.info(f"📊 벡터 차원: {embeddings_list[0]['vector'].shape}") # (768,) 확인용
    except Exception as e:
        logger.error(f"❌ 저장 실패: {e}")

if __name__ == "__main__":
    # 1. 모델 로드
    model, processor, device = load_model()
    
    if model:
        # 2. 임베딩 생성
        embeddings = process_images(model, processor, device)
        
        # 3. 파일 저장
        save_embeddings(embeddings)