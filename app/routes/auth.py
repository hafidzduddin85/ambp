# app/routes/auth.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.models.user import User
from app.database.dependencies import get_db
from app.utils.auth import verify_password  # ✅ Import fungsi verifikasi password yang benar

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(username=username).first()

    # ✅ Ganti dengan fungsi yang benar untuk verifikasi hashed password
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Username atau password salah"
        })

    # ✅ Simpan data user di session (gunakan role juga kalau ada)
    request.session["user"] = user.username
    request.session["role"] = user.role

    return RedirectResponse(url="/home", status_code=302)

@router.api_route("/logout", methods=["GET", "POST"])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
