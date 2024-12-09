from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    fullname: str
    #username: str
    email: str
    profile_picture: str

    class Config:
        orm_mode = True
