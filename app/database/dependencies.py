# app/database/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.auth import verify_token

security = HTTPBearer()

def get_db():
    """Database dependency - placeholder for future database integration"""
    # This is a placeholder for database connection
    # Currently using Google Sheets as data source
    return None

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