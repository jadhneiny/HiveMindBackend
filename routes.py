from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
from models import Chat, Course, Message, User
from schema import ChatCreate, CourseRead, MessageCreate, ChatResponse, MessageResponse, UserRead
from typing import List
import logging


router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
   # return pwd_context.verify(plain_password, hashed_password)
       # Temporarily disable hashing for testing
    return plain_password == hashed_password

# Login
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        print(f"Login request received for username: {form_data.username}")
        user = db.query(User).filter(User.username == form_data.username).first()
        print(f"Queried user: {user}")
        
        if not user:
            print("User not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(form_data.password, user.password):
            print("Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print("Password verification succeeded")
        return {"access_token": user.id, "token_type": "bearer"}
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )



# Create a new chat
@router.post("/chats/", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate, db: Session = Depends(get_db)):
    # Ensure both tutor and student exist
    tutor = db.query(User).filter(User.id == chat_data.tutor_id, User.isTutor == True).first()
    student = db.query(User).filter(User.id == chat_data.student_id, User.isTutor == False).first()
    if not tutor or not student:
        raise HTTPException(status_code=400, detail="Invalid tutor or student ID")

    # Check if chat already exists
    existing_chat = db.query(Chat).filter_by(tutor_id=chat_data.tutor_id, student_id=chat_data.student_id).first()
    if existing_chat:
        return existing_chat

    # Create new chat
    new_chat = Chat(tutor_id=chat_data.tutor_id, student_id=chat_data.student_id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat


# Send a message
@router.post("/messages/", response_model=MessageResponse)
async def send_message(message_data: MessageCreate, db: Session = Depends(get_db)):
    # Ensure chat exists
    chat = db.query(Chat).filter(Chat.id == message_data.chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Ensure sender is part of the chat
    if message_data.sender_id not in [chat.tutor_id, chat.student_id]:
        raise HTTPException(status_code=403, detail="Sender not part of this chat")

    # Create message
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

# Get all users
@router.get("/users", response_model=List[UserRead])
async def get_users(db: Session = Depends(get_db)):
    try:
        users = db.query(User).all()
        logger.info(f"Fetched users: {users}")
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/test-db")
async def test_db_connection(db: Session = Depends(get_db)):
    try:
        # Use SQLAlchemy's `text` to wrap the raw SQL query
        db.execute(text("SELECT 1"))
        return {"message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

#testing
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
        # Find the course by name
        course = db.query(Course).filter(Course.name == course_name).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Find tutors for the given course
        tutors = db.query(User).filter(User.isTutor == True).all()

        # Return the list of tutors
        return tutors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
