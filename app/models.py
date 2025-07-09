from sqlalchemy import Column, Integer, String
from app.database import Base, engine
from passlib.hash import argon2

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")  # 'admin' or 'user'
    
    def verify_password(self, plain_password):
        return argon2.verify(plain_password, self.password_hash)

    @staticmethod
    def hash_password(password):
        return argon2.hash(password)

# Table creation should be handled in your application entry point, not in the model definition file.
