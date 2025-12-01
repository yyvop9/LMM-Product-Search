import sys
import os
import pickle
import logging
import torch
import numpy as np
from PIL import Image
from pathlib import Path
from sqlalchemy.orm import Session
from transformers import CLIPProcessor, CLIPModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal
from app.models import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorGen")

BASE_DIR = Path("/data") if os.path.exists("/data") else Path(__file__).resolve().parent.parent.parent / "data"
IMAGE_DIR = BASE_DIR / "images"
OUTPUT_PATH = BASE_DIR / "product_vectors.pkl"

MODEL_ID = "openai/clip-vit-large-patch14"

def regenerate_vectors():
    db: Session = SessionLocal()
    products = db.query(Product).all()
    logger.info(f"📂 DB 발견: {len(products)}개. 로컬 벡터 생성 시작...")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model = CLIPModel.from_pretrained(MODEL_ID).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_ID)
    except Exception as e:
        logger.error(f"모델 로드 실패: {e}")
        return

    embeddings_list = []
    count = 0

    for product in products:
        try:
            image_path = IMAGE_DIR / product.image_file
            if not image_path.exists(): continue

            image = Image.open(image_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            
            vector_np = image_features.squeeze().cpu().numpy()
            embeddings_list.append({'id': str(product.id), 'vector': vector_np})
            count += 1
            if count % 50 == 0: print(f"-> {count}개 완료")
        except Exception as e:
            logger.error(f"Err: {e}")

    if embeddings_list:
        with open(OUTPUT_PATH, 'wb') as f: pickle.dump(embeddings_list, f)
        logger.info(f"🎉 완료! 총 {len(embeddings_list)}개 저장됨.")
    
    db.close()

if __name__ == "__main__":
    regenerate_vectors()