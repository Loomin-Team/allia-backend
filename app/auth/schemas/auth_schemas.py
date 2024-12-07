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

class UserSchemaResponse(BaseModel):
    id: int
    fullname: str
    username: str
    email: EmailStr
    registered: bool

    class Config:
        orm_mode = True
