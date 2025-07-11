# app/utils/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database.database import Base
import hashlib
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# SQLAlchemy Models for Database
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return self.password_hash == self.hash_password(password)
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

# Pydantic Models for API
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Asset(BaseModel):
    id: Optional[str] = None
    item_name: str
    category: str
    type: str
    manufacture: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    asset_tag: Optional[str] = None
    company: str
    bisnis_unit: Optional[str] = None
    location: str
    room_location: str
    notes: Optional[str] = None
    condition: Optional[str] = None
    purchase_date: str
    purchase_cost: str
    warranty: str = "No"
    supplier: Optional[str] = None
    journal: Optional[str] = None
    owner: str
    status: str = "Active"