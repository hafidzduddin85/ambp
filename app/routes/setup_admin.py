# app/routes/setup_admin.py

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from passlib.hash import argon2

from app.database.database import SessionLocal
from app.utils.models import User

router = APIRouter()

@router.get("/setup-admin", response_class=HTMLResponse)
def auto_create_admin():
    db: Session = SessionLocal()

    # Cek apakah sudah ada user dengan username adminasset
    existing = db.query(User).filter_by(username="adminasset").first()
    if existing:
        db.close()
        return HTMLResponse("<h3>✅ User <strong>adminasset</strong> already exists.</h3>")

    # Buat user admin baru
    admin_user = User(
        username="adminasset",
        hashed_password=argon2.hash("assetadmin"),
        role="admin"
    )
    db.add(admin_user)
    db.commit()
    db.close()

    return HTMLResponse("<h3>✅ Admin user <strong>adminasset</strong> successfully created!</h3>")
