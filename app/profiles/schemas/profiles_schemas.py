from pydantic import BaseModel, EmailStr
from typing import Optional

class UpdateProfileRequest(BaseModel):
    fullname: Optional[str]
   # username: Optional[str]

class UpdatePhotoRequest(BaseModel):
    profile_picture: Optional[str]

