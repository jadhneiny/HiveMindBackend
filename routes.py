from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
from database import get_db
from models import Chat, Course, Message, User
from schema import ChatCreate, CourseRead, MessageCreate, ChatResponse, MessageResponse, UserRead
from typing import List
import logging

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Login endpoint
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user or not verify_password(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"access_token": user.id, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

# Create a new chat
@router.post("/chats/", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate, db: Session = Depends(get_db)):
    tutor = db.query(User).filter(User.id == chat_data.tutor_id, User.isTutor == True).first()
    student = db.query(User).filter(User.id == chat_data.student_id, User.isTutor == False).first()
    if not tutor or not student:
        raise HTTPException(status_code=400, detail="Invalid tutor or student ID")

    existing_chat = db.query(Chat).filter_by(tutor_id=chat_data.tutor_id, student_id=chat_data.student_id).first()
    if existing_chat:
        return existing_chat

    new_chat = Chat(tutor_id=chat_data.tutor_id, student_id=chat_data.student_id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

# Send a message
@router.post("/messages/", response_model=MessageResponse)
async def send_message(message_data: MessageCreate, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == message_data.chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if message_data.sender_id not in [chat.tutor_id, chat.student_id]:
        raise HTTPException(status_code=403, detail="Sender not part of this chat")

    message = Message(
        chat_id=message_data.chat_id,
        sender_id=message_data.sender_id,
        content=message_data.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

# Get all chats for a user
@router.get("/chats/{user_id}", response_model=List[ChatResponse])
async def get_user_chats(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chats = db.query(Chat).filter((Chat.tutor_id == user_id) | (Chat.student_id == user_id)).all()
    return chats

# Get messages for a chat
@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).all()
    return messages

logger = logging.getLogger("uvicorn.error")

# Get all users with course name included
@router.get("/users", response_model=List[UserRead])
async def get_users(db: Session = Depends(get_db)):
    try:
        users = (
            db.query(User)
            .options(joinedload(User.course))  # Use joinedload to load the related course
            .all()
        )
        user_data = []
        for user in users:
            user_dict = user.__dict__
            course = db.query(Course).filter(Course.id == user.course_id).first()
            user_dict["course_name"] = course.name if course else None
            user_data.append(user_dict)
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}"
        )


@router.get("/test-db")
async def test_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@router.post("/test-login")
async def test_login(db: Session = Depends(get_db)):
    try:
        user = db.query(User).first()
        if user:
            return {"username": user.username, "password": user.password}
        else:
            return {"error": "No users found"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/courses", response_model=List[CourseRead])
async def get_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    if not courses:
        raise HTTPException(status_code=404, detail="No courses available")
    return courses

# Get tutors by course name
@router.get("/courses/{course_name}/tutors", response_model=List[UserRead])
async def get_tutors_by_course(course_name: str, db: Session = Depends(get_db)):
    try:
        # Step 1: Find the course by name
        course = db.query(Course).filter(Course.name == course_name).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Step 2: Find tutors who teach this course
        tutors = db.query(User).filter(User.isTutor == True, User.course_id == course.id).all()
        tutor_data = []
        for tutor in tutors:
            tutor_dict = tutor.__dict__
            tutor_dict["course_name"] = course.name
            tutor_data.append(tutor_dict)
        return tutor_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Get all users with their courses
@router.get("/users_with_courses", response_model=List[UserRead])
async def get_users_with_courses(db: Session = Depends(get_db)):
    try:
        users = db.query(
            User.id, 
            User.username, 
            User.email, 
            User.isTutor, 
            Course.name.label("course_name")
        ).join(Course, User.course_id == Course.id).all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
