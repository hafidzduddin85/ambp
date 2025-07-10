from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text  # ✅ tambahkan ini
from app.database.dependencies import get_db

router = APIRouter()

@router.get("/init_add", include_in_schema=True)
def add_columns(db: Session = Depends(get_db)):
    sql = text("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS hashed_password TEXT,
        ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user',
        ADD COLUMN IF NOT EXISTS is_active TEXT DEFAULT 'true';
    """)  # ✅ gunakan sqlalchemy.text

    try:
        db.execute(sql)
        db.commit()
        return {"message": "Columns added successfully"}
    except Exception as e:
        return {"error": str(e)}
