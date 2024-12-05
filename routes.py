from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schema
from .database import SessionLocal, engine

# Initialize the database tables
models.Base.metadata.create_all(bind=engine)

router = APIRouter()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users", response_model=schema.UserResponse)
def create_user(user: schema.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = models.User(
        username=user.username,
        password=user.password,  # In production, hash passwords before storing them
        name=user.name,
        is_tutor=user.is_tutor
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/users", response_model=list[schema.UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
