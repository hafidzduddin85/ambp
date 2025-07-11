# app/routes/setup_admin.py

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.utils.models import User

router = APIRouter()

@router.get("/setup_admin", response_class=HTMLResponse)
def setup_admin():
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter_by(username="adminasset").first()
        if existing:
            return HTMLResponse("<h3>ℹ️ Admin user 'adminasset' already exists.</h3>")

        new_user = User(
            username="adminasset",
            password_hash=User.hash_password("assetadmin123"),  # Use a secure password
            email="m.hafidz@tog.co.id",
            full_name="Admin Asset",
            role="admin",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        return HTMLResponse("<h3>✅ Admin user 'adminasset' successfully created.</h3>")
    except Exception as e:
        db.rollback()
        return HTMLResponse(f"<h3>❌ Failed to create admin user: {str(e)}</h3>", status_code=500)
    finally:
        db.close()
