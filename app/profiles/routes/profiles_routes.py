from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.profiles.schemas.profiles_schemas import UpdateProfileRequest, UpdatePhotoRequest
from app.profiles.services.profiles_services import ProfileService
from app.config.db import get_db
from app.users.schemas.user_schemas import UserResponse

profiles = APIRouter()
endpoint = "/profiles"

# @profiles.put(endpoint + "/{user_id}", response_model=UserResponse, tags=["Profiles"])
# async def update_profile_info(user_id: int, update_data: UpdateProfileRequest, db: Session = Depends(get_db)):
#     user = ProfileService.update_profile(user_id, update_data, db)
#     return user

@profiles.patch(endpoint + "/{user_id}/photo", response_model=UserResponse, tags=["Profiles"])
async def update_profile_photo(user_id: int, update_data: UpdatePhotoRequest, db: Session = Depends(get_db)):
    user = ProfileService.update_profile_photo(user_id, update_data, db)
    return user  
