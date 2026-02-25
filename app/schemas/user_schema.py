from pydantic import BaseModel, EmailStr
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "guest"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
        email: EmailStr
        password: str