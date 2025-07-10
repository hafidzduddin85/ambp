# app/routes/devtools.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.dependencies import get_db

router = APIRouter()

@router.get("/init_add", include_in_schema=True)  # hapus Depends(get_current_user)
def add_columns(db: Session = Depends(get_db)):
    sql = """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS hashed_password TEXT,
    ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user',
    ADD COLUMN IF NOT EXISTS is_active TEXT DEFAULT 'true';
    """
    try:
        db.execute(sql)
        db.commit()
        return {"message": "Columns added successfully"}
    except Exception as e:
        return {"error": str(e)}
