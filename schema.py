from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_tutor: bool

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    is_tutor: bool

    class Config:
        orm_mode = True
