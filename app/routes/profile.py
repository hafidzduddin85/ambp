from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.dependencies import get_current_user, get_db
from app.utils.models import User
from app.utils.flash import flash as set_flash

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/change-password")
def change_password_form(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("change_password.html", {"request": request, "error": ""})

@router.post("/change-password")
def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if not user.verify_password(old_password):
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "Password lama salah"})

    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "Password baru tidak cocok"})

    user.password_hash = User.hash_password(new_password)
    db.commit()

    set_flash(request, "Password berhasil diubah", "success")
    return RedirectResponse(url="/home", status_code=303)