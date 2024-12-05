from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import User
from schema import UserCreate, UserRead
from database import get_db

router = APIRouter()

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
