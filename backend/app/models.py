from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

# 1. 사용자 테이블
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 2. 상품 테이블
class Product(Base):
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True) # UUID 사용
    product_name = Column(String(255))
    description = Column(Text)
    brand = Column(String(100))
    color = Column(String(100))
    size = Column(String(100))
    price = Column(Integer)
    season = Column(String(100))
    image_file = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 3. 찜 목록 테이블 (중간 테이블)
class Wishlist(Base):
    __tablename__ = "wishlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ORM 관계 설정 (데이터 조회 시 편리함)
    product = relationship("Product")
    user = relationship("User")