# app/routes/profile.py

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database.dependencies import get_current_user, get_db
from app.models.user import User  # Ini SQLAlchemy model
from app.utils.flash import flash as set_flash
from app.utils.auth import verify_password, hash_password  # Tambahkan ini

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/change-password")
def change_password_form(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("change_password.html", {
        "request": request,
        "error": "",
        "user": user
    })

@router.post("/change-password")
def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Ambil user dari DB
    db_user = db.query(User).filter_by(username=current_user["username"]).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if not verify_password(old_password, db_user.hashed_password):
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "error": "Password lama salah",
            "user": current_user
        })

    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "error": "Password baru tidak cocok",
            "user": current_user
        })

    db_user.hashed_password = hash_password(new_password)
    db.commit()

    set_flash(request, "✅ Password berhasil diubah", "success")
    return RedirectResponse(url="/home", status_code=303)
