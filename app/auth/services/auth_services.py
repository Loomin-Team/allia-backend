from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.auth.models.user_model import User
from app.auth.schemas.auth_schemas import Token, UserSchemaPost, CreateUserRequest
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

# Cargar variables de entorno
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthServices:
    @staticmethod
    def authenticate_user(email: str, password: str, db: Session):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None  # En lugar de devolver False
        if not bcrypt_context.verify(password, user.password):
            return None  # En lugar de devolver False
        return user

    @staticmethod
    async def sign_up(create_user_request: UserSchemaPost, db: Session):
        existing_user = db.query(User).filter(User.email == create_user_request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email ya registrado.")
        
        hashed_password = bcrypt_context.hash(create_user_request.password.encode("utf-8"))
        
        new_user = User(
            fullname=create_user_request.fullname,
            email=create_user_request.email,
            password=hashed_password,
            profile_picture="",
            registered=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generar el token JWT
        token = AuthServices.create_access_token(new_user.email, new_user.id, new_user.registered, timedelta(hours=1))
        return Token(access_token=token, token_type="bearer")

    @staticmethod
    async def sign_in(create_user_request: CreateUserRequest, db: Session):
        user = AuthServices.authenticate_user(create_user_request.email, create_user_request.password, db)
        if not user:
            raise HTTPException(status_code=401, detail="Email o contraseña inválidos.")
        token = AuthServices.create_access_token(user.email, user.id, user.registered, timedelta(hours=1))
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "fullName": user.fullname,
                "email": user.email,
            }
        }

    @staticmethod
    def create_access_token(email: str, user_id: int, registered: bool, expires_delta: timedelta):
        to_encode = {"sub": email, "user_id": user_id, "registered": registered}
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
