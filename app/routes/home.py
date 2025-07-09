from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Dependency: ambil DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Root: redirect ke /home
@router.get("/", response_class=HTMLResponse)
def root_redirect():
    return RedirectResponse(url="/home")


# Home page (login required)
@router.get("/home", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        return RedirectResponse(url="/login")

    user = db.query(User).filter_by(username=username).first()
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user
    })
