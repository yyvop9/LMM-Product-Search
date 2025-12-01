from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from .. import database, models
from .products import ProductResponse # 상품 응답 스키마 재사용

router = APIRouter(
    prefix="/wishlist",
    tags=["wishlist"]
)

# 찜하기 요청 스키마
class WishlistRequest(BaseModel):
    product_id: str

# 1. 찜 목록 조회 (GET) - 핵심 수정!
# Wishlist 테이블이 아니라, Wishlist에 들어있는 'Product' 정보를 리턴함
@router.get("/", response_model=List[ProductResponse])
def get_wishlist(db: Session = Depends(database.get_db)):
    user_id = 1  # 테스트용 하드코딩
    
    # [SQL Logic] 
    # SELECT p.* FROM products p JOIN wishlists w ON p.id = w.product_id WHERE w.user_id = 1
    wishlist_products = (
        db.query(models.Product)
        .join(models.Wishlist, models.Product.id == models.Wishlist.product_id)
        .filter(models.Wishlist.user_id == user_id)
        .all()
    )
    
    return wishlist_products

# 2. 찜 추가/삭제 토글 (POST)
@router.post("/toggle")
def toggle_wishlist(req: WishlistRequest, db: Session = Depends(database.get_db)):
    user_id = 1
    
    # 이미 찜했는지 확인
    existing = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == user_id,
        models.Wishlist.product_id == req.product_id
    ).first()
    
    if existing:
        # 이미 있으면 삭제 (찜 취소)
        db.delete(existing)
        db.commit()
        return {"status": "removed", "message": "찜 목록에서 삭제되었습니다."}
    else:
        # 없으면 추가 (찜하기)
        # 상품이 실제로 존재하는지 확인 (Foreign Key 오류 방지)
        product = db.query(models.Product).filter(models.Product.id == req.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        new_item = models.Wishlist(user_id=user_id, product_id=req.product_id)
        db.add(new_item)
        db.commit()
        return {"status": "added", "message": "찜 목록에 추가되었습니다."}

# 3. 찜 여부 확인 (단일 상품)
@router.get("/check/{product_id}")
def check_wishlist_status(product_id: str, db: Session = Depends(database.get_db)):
    user_id = 1
    exists = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == user_id,
        models.Wishlist.product_id == product_id
    ).first()
    return {"is_in_wishlist": bool(exists)}