# app/utils/auth.py

import os
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict

from passlib.context import CryptContext
from jwt import PyJWTError

# Konfigurasi token
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

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
    Generate JWT token dari data user.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[Dict]:
    """
    Verifikasi token dan return payload user jika valid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
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
