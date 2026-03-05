from pydantic import BaseModel, EmailStr
from pydantic import BaseModel

from app.models.user import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Role = Role.GUEST


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
        email: EmailStr
        password: str