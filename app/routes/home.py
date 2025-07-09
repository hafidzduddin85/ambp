# app/routes/home.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.routes.dependencies import get_current_user
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def root_redirect():
    return RedirectResponse(url="/home")

@router.get("/home", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(SessionLocal)):
    username = request.session.get("user")
    if not username:
        return RedirectResponse(url="/login")
    user = db.query(User).filter_by(username=username).first()
    return templates.TemplateResponse("home.html", {"request": request, "user": user})
