# auth.py
from passlib.context import CryptContext
from typing import Optional

# Create a password hashing context with Argon2
pwd_context = CryptContext(schemes=["argon2"], default="argon2", deprecated="auto")

def hash_password(password: Optional[str]) -> Optional[str]:
    """Hash plain text password."""
    if password is None:
        return None
    return pwd_context.hash(password)

def verify_password(plain_password: Optional[str], hashed_password: Optional[str]) -> bool:
    """Verify if plain password matches hashed password."""
    if plain_password is None or hashed_password is None:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Log the exception if needed
        return False

