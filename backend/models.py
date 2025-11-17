from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text)
    email = Column(Text, unique=True, index=True)
    password_hash = Column(Text)
    role = Column(Text, default="user")  # user/admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    url = Column(Text)
    status = Column(Text, default="queued")  # queued, processing, done, failed
    result = Column(JSON)
    job_id = Column(Text, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

class TrainingCase(Base):
    __tablename__ = "training_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text)
    description = Column(Text)
    payload_url = Column(Text)
    lesson = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

