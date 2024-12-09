from pydantic import BaseModel, EmailStr
from app.auth.models.user_model import User

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict 



class UserSchemaPost(BaseModel):
    fullname: str  
    email: EmailStr 
    password: str  

    class Config:
        orm_mode = True 
