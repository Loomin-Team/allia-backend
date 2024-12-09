
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.users.schemas.user_schemas import UserResponse
from app.config.db import get_db

users = APIRouter()

# Endpoint para obtener todos los usuarios (requiere autenticación)
@users.get("/users", response_model=list[UserResponse], tags=["Users"])
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@users.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user

@users.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return None
