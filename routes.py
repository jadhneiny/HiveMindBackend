from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Chat, Message, User
from schema import ChatCreate, MessageCreate
from typing import List

router = APIRouter()

# Create a new chat
@router.post("/chats/", response_model=dict)
async def create_chat(tutor_id: int, student_id: int, db: Session = Depends(get_db)):
    # Ensure both tutor and student exist
    tutor = db.query(User).filter(User.id == tutor_id, User.is_tutor == True).first()
    student = db.query(User).filter(User.id == student_id, User.is_tutor == False).first()
    if not tutor or not student:
        raise HTTPException(status_code=400, detail="Invalid tutor or student ID")

    # Check if chat already exists
    existing_chat = db.query(Chat).filter_by(tutor_id=tutor_id, student_id=student_id).first()
    if existing_chat:
        return {"message": "Chat already exists", "chat_id": existing_chat.id}

    # Create new chat
    new_chat = Chat(tutor_id=tutor_id, student_id=student_id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return {"message": "Chat created", "chat_id": new_chat.id}


# Send a message
@router.post("/messages/", response_model=dict)
async def send_message(chat_id: int, sender_id: int, content: str, db: Session = Depends(get_db)):
    # Ensure chat exists
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Ensure sender is part of the chat
    if sender_id not in [chat.tutor_id, chat.student_id]:
        raise HTTPException(status_code=403, detail="Sender not part of this chat")

    # Create message
    message = Message(chat_id=chat_id, sender_id=sender_id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"message": "Message sent", "message_id": message.id}


# Get all chats for a user
@router.get("/chats/{user_id}", response_model=List[dict])
async def get_user_chats(user_id: int, db: Session = Depends(get_db)):
    chats = db.query(Chat).filter((Chat.tutor_id == user_id) | (Chat.student_id == user_id)).all()
    return [{"id": chat.id, "tutor_id": chat.tutor_id, "student_id": chat.student_id, "created_at": chat.created_at} for chat in chats]


# Get messages for a chat
@router.get("/chats/{chat_id}/messages", response_model=List[dict])
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).all()
    return [{"id": msg.id, "sender_id": msg.sender_id, "content": msg.content, "timestamp": msg.timestamp} for msg in messages]

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
