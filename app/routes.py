from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.database import get_db
from api.models import User
from api.schema import UserCreate, UserResponse

user_routes = APIRouter()

@user_routes.get("/", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@user_routes.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if the username already exists
    result = await db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create the new user
    new_user = User(
        username=user.username,
        password=user.password,  # Hash the password in a real app!
        name=user.name,
        is_tutor=user.is_tutor
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
