from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, get_db
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserResponse
from app.schemas.user_schema import UserLogin
from app.core.security import verify_password, create_access_token
from sqlalchemy import select
from app.models.user import User
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
app = FastAPI(
    title="SeatFlow API",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)
security = HTTPBearer()

@app.get("/")
def root():
    return {
        "message": "SeatFlow API is running",
        "database_url": settings.DATABASE_URL
    }

@app.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    user = UserService.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,  # NICHT password_hash mehr
        role=user_data.role
    )

    db.commit()
    db.refresh(user)

    return user

@app.post("/login")
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    stmt = select(User).where(User.email == user_data.email)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return {"error": "Invalid credentials"}

    if not verify_password(user_data.password, user.password_hash):
        return {"error": "Invalid credentials"}

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    stmt = select(User).where(User.id == int(user_id))
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }