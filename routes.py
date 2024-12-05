from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
from models import Chat, Message, User
from schema import ChatCreate, MessageCreate, ChatResponse, MessageResponse, UserRead
from typing import List

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Login
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": user.id, "token_type": "bearer"}

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


# Get all users
@router.get("/users", response_model=List[UserRead])
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/test-db")
async def test_db_connection(db: Session = Depends(get_db)):
    try:
        # Test query
        result = db.execute("SELECT 1").fetchone()
        return {"db_status": "connected", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")
