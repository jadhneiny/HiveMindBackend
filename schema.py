from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatCreate(BaseModel):
    tutor_id: int
    student_id: int


class MessageCreate(BaseModel):
    chat_id: int
    sender_id: int
    content: str


class ChatResponse(BaseModel):
    id: int
    tutor_id: int
    student_id: int
    created_at: datetime


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    timestamp: datetime


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
