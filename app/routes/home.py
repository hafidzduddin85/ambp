from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Root: redirect ke /home atau /login
@router.get("/", response_class=RedirectResponse)
def root(request: Request):
    user = request.session.get("user")
    if user is None:
        return RedirectResponse(url="/login")
    else:
        return RedirectResponse(url="/home")

# Home page (login required)
@router.get("/home", response_class=HTMLResponse)
def home(request: Request, current_user: User = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": current_user}
    )

