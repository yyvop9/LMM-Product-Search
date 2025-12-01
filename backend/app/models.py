from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

# 1. 사용자 테이블 (User)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)  # [New] 회원가입 시 이름 저장
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정 (유저가 찜한 목록)
    wishlist = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")

# 2. 상품 테이블 (Product)
class Product(Base):
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True) # UUID 사용
    product_name = Column(String(255), index=True)
    description = Column(Text, nullable=True)
    
    # 상세 속성
    brand = Column(String(100), nullable=True)
    price = Column(Integer, nullable=True)
    color = Column(String(100), nullable=True)
    size = Column(String(100), nullable=True)
    
    # 검색 필터링용 핵심 컬럼
    season = Column(String(100), nullable=True) # 예: Spring, Summer...
    gender = Column(String(50), nullable=True)  # 예: Men, Women, Unisex
    category = Column(String(100), nullable=True) # 예: Top, Bottom, Outer
    
    image_file = Column(String(255), nullable=False) # 이미지 파일명
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정 (이 상품을 찜한 내역)
    wishlisted_by = relationship("Wishlist", back_populates="product")

# 3. 찜 목록 테이블 (Wishlist - User와 Product의 중간 테이블)
class Wishlist(Base):
    __tablename__ = "wishlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ORM 관계 설정 (데이터 조회 시 편리함)
    user = relationship("User", back_populates="wishlist")
    product = relationship("Product", back_populates="wishlisted_by")