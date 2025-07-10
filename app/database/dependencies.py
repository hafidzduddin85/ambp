# app/database/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.utils.auth import verify_token
from app.database.database import SessionLocal

security = HTTPBearer()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from session or token"""
    # Check session first
    user = request.session.get("user")
    if user:
        return user
    
    # Check token if no session
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            return payload
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_admin_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user and verify admin role"""
    user = get_current_user(request, credentials)
    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

def get_admin_user(user=Depends(get_current_user)):
    """Allow only admin user"""
    if user and user.get("role") == "admin":
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this resource.",
    )
