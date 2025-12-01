import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from dotenv import load_dotenv

from .. import database, models

# .env 파일 로드
load_dotenv()

# --- 설정 (환경변수에서 로드) ---
# .env에 없으면 기본값(테스트용) 사용, 실제 운영 시엔 꼭 .env를 확인하세요.
SECRET_KEY = os.getenv("SECRET_KEY", "modify_project_super_secret_key_2024")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

# --- 보안 도구 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter(prefix="/auth", tags=["authentication"])

# --- Pydantic Schemas (입출력 데이터 모델) ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str  # [New] 회원가입 시 이름 필수

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str  # 프론트엔드 환영 메시지용

# --- Helper Functions (보안 로직) ---
def verify_password(plain_password, hashed_password):
    """입력된 비밀번호와 DB의 해시 비밀번호 비교"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """비밀번호 암호화 (Hashing)"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- API Endpoints ---

# 1. 회원가입 (Sign Up)
@router.post("/signup", status_code=201)
def signup(user: UserCreate, db: Session = Depends(database.get_db)):
    # 이메일 중복 체크
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일 주소입니다.")
    
    # 비밀번호 해싱 후 저장
    hashed_pw = get_password_hash(user.password)
    
    new_user = models.User(
        email=user.email,
        full_name=user.full_name, # 이름 저장
        password_hash=hashed_pw,
        is_admin=False 
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "회원가입 성공", "email": new_user.email}

# 2. 로그인 (Login) -> JWT 발급
@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(database.get_db)):
    # 사용자 확인 (이메일 검색)
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        # 보안을 위해 '이메일 없음'과 '비번 틀림' 메시지를 통일하는 것이 좋음
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    # 비밀번호 검증
    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    # 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email},
        expires_delta=access_token_expires
    )
    
    # 로그인한 사용자의 이름(full_name)이 없으면 이메일 앞부분 사용
    display_name = db_user.full_name if db_user.full_name else db_user.email.split("@")[0]
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_name": display_name
    }

# 3. 현재 로그인한 사용자 정보 가져오기 (Dependency)
# 사용법: @router.get("/me") def read_me(current_user: models.User = Depends(get_current_user)):
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 검증할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 토큰 복호화
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # DB에서 사용자 조회
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user