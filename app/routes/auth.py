# app/routes/auth.py
from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.dependencies import get_db

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return HTMLResponse(template_name="login.html", context={"request": request, "error": ""})

@router.post("/login")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return HTMLResponse(template_name="login.html", context={"request": request, "error": "Username atau password salah"})
    request.session["user"] = user.username
    return RedirectResponse(url="/home", status_code=302)

@router.api_route("/logout", methods=["GET", "POST"])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
