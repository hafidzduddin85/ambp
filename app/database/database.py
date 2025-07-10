# app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Ambil DATABASE_URL dari environment (atau pakai default SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Buat engine SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Buat session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk deklarasi ORM model
Base = declarative_base()

# Fungsi init_db
def init_db():
    from app.models import user  # pastikan semua model di-import di sini
    Base.metadata.create_all(bind=engine)
