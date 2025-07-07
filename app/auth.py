# auth.py
from passlib.context import CryptContext

# Create a password hashing context with Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash plain text password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if plain password matches hashed password."""
    return pwd_context.verify(plain_password, hashed_password)
