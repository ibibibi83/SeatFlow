from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password
class UserService:

    @staticmethod
    def create_user(db: Session, email: str, password: str, role: str = "guest") -> User:
        hashed_pw = hash_password(password)

        user = User(
            email=email,
            password_hash=hashed_pw,
            role=role
        )

        db.add(user)
        return user


