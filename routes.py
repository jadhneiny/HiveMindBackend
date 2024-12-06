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
logger = logging.getLogger("uvicorn.error")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    # return pwd_context.verify(plain_password, hashed_password)
    # Temporarily bypass password hashing for testing
    return plain_password == hashed_password

# Login endpoint
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login with plaintext password comparison (for testing).
    """
    try:
        # logger.info(f"Login attempt for username: {form_data.username}")
        
        # Retrieve the user from the database
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user:
            logger.warning(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify the password (plaintext or hashed based on your setup)
        if not verify_password(form_data.password, user.password):
            logger.warning(f"Password mismatch for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # logger.info(f"Login successful for username: {form_data.username}")
        return {"access_token": user.id, "token_type": "bearer"}

    except HTTPException as e:
        raise e  # Re-raise expected HTTP exceptions

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
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
from sqlalchemy.orm import joinedload

from sqlalchemy.orm import joinedload
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Chat, User
router = APIRouter()

@router.get("/chats/{user_id}")
async def get_user_chats(user_id: int, db: Session = Depends(get_db)):
    try:
        # Fetch the user to verify they exist and determine their role
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Query the chats and include tutor and student details
        chats = (
            db.query(Chat)
            .join(User, Chat.tutor_id == User.id, isouter=True)
            .join(User, Chat.student_id == User.id, isouter=True)
            .filter((Chat.student_id == user_id) | (Chat.tutor_id == user_id))
            .all()
        )

        # Construct the response
        response = []
        for chat in chats:
            chat_data = {
                "id": chat.id,
                "tutor_id": chat.tutor_id,
                "tutor_name": chat.tutor.username if chat.tutor else None,
                "student_id": chat.student_id,
                "student_name": chat.student.username if chat.student else None,
                "created_at": chat.created_at,
            }

            # Include only the relevant name based on user role
            if user.id == chat.tutor_id:
                # If the user is a tutor, include only the student's name
                chat_data.pop("tutor_name")
            elif user.id == chat.student_id:
                # If the user is a student, include only the tutor's name
                chat_data.pop("student_name")

            response.append(chat_data)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chats: {str(e)}")



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

# Get all users with their associated courses
@router.get("/users_with_courses", response_model=List[UserRead])
async def get_users_with_courses(db: Session = Depends(get_db)):
    """
    Retrieve all users with their associated courses.
    """
    try:
        # Use joinedload to fetch the related course data eagerly
        users = db.query(User).options(joinedload(User.course)).all()

        # Build the response with user details and associated course name
        users_with_courses = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "isTutor": user.isTutor,
                "course_name": user.course.name if user.course else None,
            }
            for user in users
        ]

        return users_with_courses
    except Exception as e:
        logger.error(f"Error in /users_with_courses: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )
    
@router.get("/tutors", response_model=List[UserRead])
async def get_tutors(db: Session = Depends(get_db)):
    """
    Fetch all tutors from the database.
    """
    try:
        logger.info("Fetching all tutors")
        tutors = db.query(User).filter(User.isTutor == True).all()

        if not tutors:
            logger.warning("No tutors found")
            return []

        # Map tutors to the `UserRead` schema
        tutor_list = [
            UserRead(
                id=tutor.id,
                username=tutor.username,
                email=tutor.email,
                isTutor=tutor.isTutor,
                course_id=tutor.course_id,
                course_name=tutor.course.name if tutor.course else None
            )
            for tutor in tutors
        ]

        logger.info(f"Tutors fetched: {len(tutor_list)} tutors found.")
        return tutor_list
    except Exception as e:
        logger.error(f"Error fetching tutors: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )


@router.get("/tutors/{name}", response_model=UserRead)
async def get_tutor_by_name(name: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching tutor with username: {name}")
        tutor = db.query(User).filter(User.username == name, User.isTutor == True).first()
        if not tutor:
            logger.error(f"Tutor with username '{name}' not found.")
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        # Explicitly construct the response model
        response = UserRead(
            id=tutor.id,
            username=tutor.username,
            email=tutor.email,
            isTutor=tutor.isTutor,
            course_id=tutor.course_id,
            course_name=tutor.course.name if tutor.course else None
        )
        logger.info(f"Tutor response: {response}")
        return response
    except Exception as e:
        logger.error(f"Unexpected error in /tutors/{name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )
