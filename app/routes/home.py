# app/routes/home.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ✅ Root: redirect ke /home jika login, jika tidak ke /login
@router.get("/", include_in_schema=False)
def root(request: Request):
    if request.session.get("user"):
        return RedirectResponse(url="/home")
    return RedirectResponse(url="/login")

# ✅ Home page: hanya bisa diakses jika login
@router.get("/home", response_class=HTMLResponse)
def home(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": current_user
    })
