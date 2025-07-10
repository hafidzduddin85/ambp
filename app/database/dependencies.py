# app/database/dependencies.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Generator, Dict, Any
import logging

from app.utils.auth import verify_token
from app.database.database import SessionLocal

# Setup logger (opsional)
logger = logging.getLogger(__name__)

# Bearer token auth (tidak otomatis error jika tidak ada token)
security = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency untuk mendapatkan sesi database SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency untuk mendapatkan user saat ini dari session atau token Bearer.
    - Jika session tersedia: prioritas utama
    - Jika tidak: gunakan token Bearer
    """
    session_user = request.session.get("user")

    # Jika user dari session adalah dict (username & role)
    if isinstance(session_user, dict) and "username" in session_user:
        return session_user

    # Jika user dari session hanya berupa username (string)
    if isinstance(session_user, str):
        return {"username": session_user, "role": "admin"}  # Default role

    # Jika tidak ada session, coba dari Bearer token
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            return payload

    # Tidak terautentikasi
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tidak terautentikasi.",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_admin_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency untuk memastikan user memiliki role admin.
    """
    if user.get("role") == "admin":
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Akses hanya untuk admin.",
    )
