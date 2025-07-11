# app/routes/reset_db.py

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.database.database import Base, engine
from app.utils.models import User

router = APIRouter()

@router.get("/reset-db", response_class=HTMLResponse)
def reset_database():
    try:
        # Hapus semua tabel
        Base.metadata.drop_all(bind=engine)

        # Buat ulang semua tabel
        Base.metadata.create_all(bind=engine)
        # Kembalikan pesan sukses
        return HTMLResponse("<h3>✅ Database reset successful: all tables dropped and recreated.</h3>")
    except Exception as e:
        return HTMLResponse(f"<h3>❌ Error resetting database: {str(e)}</h3>", status_code=500)
