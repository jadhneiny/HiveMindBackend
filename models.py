from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey("users.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())

    tutor = relationship("User", foreign_keys=[tutor_id])
    student = relationship("User", foreign_keys=[student_id])


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())

    chat = relationship("Chat")
    sender = relationship("User")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    isTutor = Column(Boolean, name="istutor", default=False)  # Match DB column name
    course_id = Column(Integer, ForeignKey("courses.id"))  # ForeignKey to courses table

    course = relationship("Course", back_populates="users", lazy="joined")  # Use lazy="joined" to fetch data eagerly


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    users = relationship("User", back_populates="course")  # Back-populates the relationship

