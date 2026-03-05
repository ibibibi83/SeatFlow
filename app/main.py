from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.seat_quota import SeatQuota
from app.services.seat_service import SeatService
from app.core.config import settings
from app.services.reservation_service import ReservationService
from app.db.base import Base
from app.db.session import engine, get_db
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserResponse, UserLogin
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user,
    require_role,

)

app = FastAPI(
    title="SeatFlow API",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)


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
    print (user_data)
    user = UserService.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
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

    if not user or not verify_password(user_data.password, user.password_hash):
        return {"error": "Invalid credentials"}

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/admin-only")
def admin_area(current_user: User = Depends(require_role("manager"))):
    return {"message": "Welcome Manager"}

@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }

@app.get("/seats")
def get_seats(db: Session = Depends(get_db)):
    quota = SeatService.get_quota(db)

    if not quota:
        quota = SeatService.create_initial_quota(db)

    reserved = ReservationService.calculate_reserved_seats(db)
    available = ReservationService.calculate_available_seats(db)

    return {
        "total_seats": quota.total_seats,
        "reserved_seats": reserved,
        "available_seats": available
    }
@app.patch("/seats")
def update_seats(
    total_seats: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager"))
):
    quota = SeatService.update_quota(db, total_seats)

    return {
        "message": "Seat quota updated",
        "total_seats": quota.total_seats
    }
from app.routes.reservation_routes import router as reservation_router

app.include_router(reservation_router)