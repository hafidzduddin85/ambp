# This file is deprecated - User model moved to app/utils/models.py
# Please import from: from app.utils.models import User
# app/models/user.py
#from sqlalchemy import Column, Integer, String
#from app.database.base import Base

#class User(Base):
#    __tablename__ = "users"
#
#    id = Column(Integer, primary_key=True, index=True)
#    username = Column(String, unique=True, index=True, nullable=False)
#    hashed_password = Column(String, nullable=False)
#    role = Column(String, default="user")
#    is_active = Column(String, default="true")
