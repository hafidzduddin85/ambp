# app/models/user.py
from sqlalchemy import Column, Integer, String
from app.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user")
    is_active = Column(String, default="true")
