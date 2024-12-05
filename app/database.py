from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Load environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy Base
Base = declarative_base()

# Async engine for PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Session maker
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with async_session() as session:
        yield session

# Initialize the database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
