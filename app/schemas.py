from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    name: str
    is_tutor: bool

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True
