from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Chat schemas
class ChatCreate(BaseModel):
    tutor_id: int
    student_id: int

class ChatResponse(BaseModel):
    id: int
    tutor_id: int
    student_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Message schemas
class MessageCreate(BaseModel):
    chat_id: int
    sender_id: int
    content: str

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

# User schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    isTutor: bool

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    isTutor: bool
    course_id: Optional[int]  # Include the course_id if it's part of the response
    course_name: Optional[str] = None  # Ensure this matches any additional processing

    class Config:
        from_attributes = True

# Course schemas
class CourseRead(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True