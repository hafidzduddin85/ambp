# app/routes/auth.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.utils.models import User
from app.database.dependencies import get_db
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
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not user.verify_password(password):
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Username atau password salah"
            })
        
        if not user.is_active:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Akun tidak aktif"
            })

        # Save user data in session
        request.session["user"] = user.username
        request.session["user_id"] = user.id
        request.session["role"] = user.role
        
        return RedirectResponse(url="/home", status_code=302)
        
    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Terjadi kesalahan sistem"
        })

@router.api_route("/logout", methods=["GET", "POST"])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
