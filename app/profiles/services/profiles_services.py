from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.auth.models.user_model import User
from app.profiles.schemas.profiles_schemas import UpdateProfileRequest, UpdatePhotoRequest
from io import BytesIO

class ProfileService:
    @staticmethod
    def update_profile(user_id: int, update_data: UpdateProfileRequest, db: Session):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if update_data.fullname:
            user.fullname = update_data.fullname
        if update_data.username:
            user.username = update_data.username

        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_profile_photo(user_id: int, update_data: UpdatePhotoRequest, db: Session):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if update_data.profile_picture:
            user.profile_picture = update_data.profile_picture

        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_fullname_by_id(user_id: int, db: Session):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.fullname
                             
