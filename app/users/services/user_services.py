from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import HTTPException, status

class UserService:
    @staticmethod
    def get_all_users(db: Session):
        return db.query(User).all()

    @staticmethod
    def get_user_by_id(user_id: int, db: Session):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def delete_user(user_id: int, db: Session):
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        db.delete(user)
        db.commit()
        return user
