# app/utils/models.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

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

class LoginRequest(BaseModel):
    username: str
    password: str