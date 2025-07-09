# app/routes/sync.py

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.models import User
from app.dependencies import get_admin_user, get_db
from app.sheets import sync_assets_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/sync-assets")
def sync_assets(
    request: Request,
    status: str = "admin",
    db: Session = Depends(get_db),
    user: User = Depends(get_admin_user)
):
    # Jalankan sinkronisasi data aset
    try:
        sync_assets_data()
        message = "Sinkronisasi aset berhasil!"
    except Exception as e:
        message = f"Gagal sinkronisasi: {str(e)}"

    users = db.query(User).filter_by(role=status).all()
    return templates.TemplateResponse("sync.html", {
        "request": request,
        "users": users,
        "status": status,
        "message": message
    })
