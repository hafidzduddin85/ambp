# === 2. dependencies.py ===
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app.models import User
from app.database import SessionLocal
from fastapi import HTTPException


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise RedirectResponse(url="/login", status_code=302)
    return user


def get_admin_user(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        raise RedirectResponse(url="/login", status_code=302)
    user = db.query(User).filter_by(username=username).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    return user