from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models.user import User
from auth.schemas.auth import CreateUserRequest, UserSchemaPost, Token
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = '197b2c371eas312ze#@1ssdsasd1123'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthServices:
    @staticmethod
    def authenticate_user(email: str, password: str, db: Session):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        if not bcrypt_context.verify(password, user.password):
            return False
        return user

    @staticmethod
    async def sign_up(create_user_request: UserSchemaPost, db: Session):
        existing_user = db.query(User).filter(User.email == create_user_request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email ya registrado.")
        
        hashed_password = bcrypt_context.hash(create_user_request.password)
        
        new_user = User(
            fullname=create_user_request.fullname,
            username=create_user_request.username,
            email=create_user_request.email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = AuthServices.create_access_token(new_user.email, new_user.id, timedelta(hours=1))
        return Token(access_token=token, token_type="bearer")

    @staticmethod
    async def sign_in(create_user_request: CreateUserRequest, db: Session):
        user = AuthServices.authenticate_user(create_user_request.email, create_user_request.password, db)
        if not user:
            raise HTTPException(status_code=401, detail="Email o contraseña inválidos.")
        
        token = AuthServices.create_access_token(user.email, user.id, timedelta(hours=1))
        return Token(access_token=token, token_type="bearer")

    @staticmethod
    def create_access_token(email: str, user_id: int, expires_delta: timedelta):
        to_encode = {"sub": email, "user_id": user_id}
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
