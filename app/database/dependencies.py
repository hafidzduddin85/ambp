# app/database/dependencies.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.utils.auth import verify_token
from app.database.database import SessionLocal

security = HTTPBearer(auto_error=False)

def get_db() -> Session:
    """
    Dependency untuk mendapatkan sesi database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Mendapatkan user dari session atau dari token Bearer.
    Prioritaskan session.
    """
    # Cek session
    session_user = request.session.get("user")
    if isinstance(session_user, dict) and "username" in session_user:
        return session_user

    # Jika tidak ada session, cek token
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            return payload

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tidak terautentikasi.",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_admin_user(user: dict = Depends(get_current_user)):
    """
    Pastikan user memiliki role admin.
    """
    if user and user.get("role") == "admin":
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Akses hanya untuk admin.",
    )
