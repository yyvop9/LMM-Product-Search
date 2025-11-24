from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, models
from .products import ProductResponse # 상품 정보 스키마 재사용

router = APIRouter(prefix="/wishlist", tags=["wishlist"])

# [Helper] 현재 유저 ID 가져오기
# 현재 프론트엔드 로그인이 시뮬레이션 상태이므로, 테스트를 위해 1번 유저로 고정합니다.
# 추후 JWT 인증 도입 시, 토큰에서 user_id를 추출하는 로직으로 교체해야 합니다.
def get_current_user_id():
    return 1 

# [API] 1. 찜 토글 (Toggle: 추가 <-> 삭제)
@router.post("/{product_id}")
def toggle_wishlist(product_id: str, db: Session = Depends(database.get_db)):
    user_id = get_current_user_id()
    
    # 1. 상품이 실제로 존재하는지 확인
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 2. 이미 찜한 상품인지 확인
    existing_item = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == user_id,
        models.Wishlist.product_id == product_id
    ).first()

    if existing_item:
        # 이미 있으면 -> 삭제 (찜 해제)
        db.delete(existing_item)
        db.commit()
        # 프론트엔드 UI 업데이트를 위해 현재 상태(False) 반환
        return {"message": "Wishlist removed", "is_liked": False}
    else:
        # 없으면 -> 추가 (찜 하기)
        new_item = models.Wishlist(user_id=user_id, product_id=product_id)
        db.add(new_item)
        db.commit()
        # 프론트엔드 UI 업데이트를 위해 현재 상태(True) 반환
        return {"message": "Wishlist added", "is_liked": True}

# [API] 2. 내 찜 목록 조회 (JOIN 쿼리 사용)
@router.get("/", response_model=List[ProductResponse])
def get_my_wishlist(db: Session = Depends(database.get_db)):
    user_id = get_current_user_id()
    
    # Wishlist 테이블에는 상품 ID만 있으므로, Product 테이블과 조인(Join)하여
    # 상품의 상세 정보(이미지, 이름, 가격 등)를 한 번에 가져옵니다.
    wishlist_items = db.query(models.Product).join(
        models.Wishlist, models.Product.id == models.Wishlist.product_id
    ).filter(models.Wishlist.user_id == user_id).all()
    
    return wishlist_items

# [API] 3. 특정 상품 찜 여부 확인 (상세 페이지용)
@router.get("/check/{product_id}")
def check_is_liked(product_id: str, db: Session = Depends(database.get_db)):
    user_id = get_current_user_id()
    
    exists = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == user_id,
        models.Wishlist.product_id == product_id
    ).first()
    
    return {"is_liked": exists is not None}