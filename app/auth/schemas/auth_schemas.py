from pydantic import BaseModel, EmailStr

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
