from pydantic import BaseModel, EmailStr

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserSchemaPost(BaseModel):
    fullname: str
    username: str
    email: EmailStr
    password: str
