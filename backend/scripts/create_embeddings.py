import sys
import os
import torch
import pickle
import logging
import pandas as pd
from PIL import Image
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from tqdm import tqdm
from transformers import CLIPProcessor, CLIPModel

# 필요한 경우 SQLAlchemy 관련 임포트 (DB 모드 사용 시)
# from app.database import SessionLocal
# from app.models import Product

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VectorPipeline")

class DataStrategy(ABC):
    """데이터 소스별(CSV vs DB) 데이터를 가져오는 추상 클래스"""
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        pass

class CsvStrategy(DataStrategy):
    """CSV 파일에서 데이터를 로드하는 전략"""
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path

    def fetch_data(self) -> List[Dict[str, Any]]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV 없음: {self.csv_path}")
        
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(self.csv_path, encoding='cp949')
        
        # 데이터 정규화하여 반환
        data = []
        for _, row in df.iterrows():
            fname = row.get('image_filename') or row.get('filename')
            if fname:
                data.append({
                    "id": str(row.get('id', fname)),
                    "filename": str(fname)
                })
        return data

class DbStrategy(DataStrategy):
    """DB에서 데이터를 로드하는 전략 (SQLAlchemy 의존성 필요)"""
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def fetch_data(self) -> List[Dict[str, Any]]:
        session = self.session_factory()
        try:
            # 실제 환경에선 app.models.Product import 필요
            # products = session.query(Product).all()
            products = [] # Dummy for demonstration without DB
            logger.info("DB 연결 및 쿼리 실행 (구현 필요)")
            
            data = []
            for p in products:
                data.append({
                    "id": str(p.id),
                    "filename": p.image_file
                })
            return data
        finally:
            session.close()

class Vectorizer:
    """CLIP 모델을 로드하고 임베딩을 수행하는 메인 클래스"""
    
    MODEL_ID = "openai/clip-vit-large-patch14"

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.image_dir = base_dir / "images"
        self.output_path = base_dir / "product_vectors.pkl"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        logger.info(f"🚀 Device: {self.device} | Model: {self.MODEL_ID}")
        # safetensors 사용 (Code A의 장점 채용)
        self.model = CLIPModel.from_pretrained(self.MODEL_ID, use_safetensors=True).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(self.MODEL_ID, use_safetensors=True)

    def run(self, strategy: DataStrategy):
        """전략(CSV/DB)에 따라 데이터를 가져와 벡터화 수행"""
        items = strategy.fetch_data()
        logger.info(f"📂 처리 대상 데이터: {len(items)}개")

        results = []
        success_cnt = 0

        for item in tqdm(items, desc="Processing"):
            try:
                img_path = self.image_dir / item['filename']
                
                # 이미지 전처리 (RGB 변환 필수)
                image = Image.open(img_path).convert("RGB")
                
                inputs = self.processor(images=image, return_tensors="pt", padding=True).to(self.device)
                
                with torch.no_grad():
                    features = self.model.get_image_features(**inputs)
                    # 정규화 (Cosine Similarity용)
                    features = features / features.norm(p=2, dim=-1, keepdim=True)
                
                vector_np = features.squeeze().cpu().numpy()
                
                results.append({
                    "id": item['id'],
                    "vector": vector_np
                })
                success_cnt += 1

            except FileNotFoundError:
                continue # 이미지 없음
            except Exception as e:
                # logger.error(f"Error processing {item['filename']}: {e}")
                pass

        self._save(results)
        logger.info(f"✨ 완료: {success_cnt}/{len(items)} 성공")

    def _save(self, data):
        with open(self.output_path, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"💾 저장됨: {self.output_path}")

if __name__ == "__main__":
    # 환경에 따른 경로 설정 (Code B의 장점 채용)
    BASE_PATH = Path("/data") if Path("/data").exists() else Path(__file__).resolve().parent.parent / "data"
    
    vectorizer = Vectorizer(base_dir=BASE_PATH)

    # 상황에 따라 전략 선택
    # CASE 1: CSV 모드
    csv_strategy = CsvStrategy(BASE_PATH / "products.csv")
    vectorizer.run(csv_strategy)

    # CASE 2: DB 모드 (필요 시 주석 해제)
    # from app.database import SessionLocal
    # db_strategy = DbStrategy(SessionLocal)
    # vectorizer.run(db_strategy)