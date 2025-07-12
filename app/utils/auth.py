# app/utils/auth.py

import os
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from passlib.context import CryptContext

# Konfigurasi token - Using Supabase JWT Secret
SECRET_KEY = os.getenv("SECRET_KEY", "your-supabase-jwt-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Supabase configuration (optional for future use)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Konfigurasi hashing pakai Argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# ========================
# JWT Access Token
# ========================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate JWT token dari data user (Supabase compatible).
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    
    # Add standard JWT claims (Supabase compatible)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "sub": str(data.get("user_id", data.get("id", ""))),  # Subject (user ID)
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_supabase_compatible_token(user_data: dict) -> str:
    """
    Create token with Supabase-style payload for future compatibility.
    """
    payload = {
        "sub": str(user_data["id"]),  # Supabase user ID format
        "email": user_data.get("email", ""),
        "role": user_data.get("role", "user"),
        "username": user_data.get("username", ""),
        "full_name": user_data.get("full_name", ""),
        "aud": "authenticated",  # Supabase audience
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[Dict]:
    """
    Verifikasi token dan return payload user jika valid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ========================
# Password Hashing
# ========================

def hash_password(password: str) -> str:
    """
    Hash password menggunakan Argon2.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifikasi password menggunakan Argon2.
    """
    return pwd_context.verify(plain_password, hashed_password)
