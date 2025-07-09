from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user
from app.models import User

router = APIRouter()


# Root: redirect ke /home
@router.get("/", response_class=RedirectResponse)
def root_redirect(request: Request):
    """
    Redirect to /home if username is set in session.
    Otherwise, redirect to /login.
    """
    username = request.session.get("user")
    if username is None:
        return RedirectResponse(url="/login")
    else:
        return RedirectResponse(url="/home")


# Home page (login required)
@router.get("/home", response_class=HTMLResponse)
def home(request: Request, user: User = Depends(get_current_user)):
    """
    Home page after login. Shows user's details.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return """
    <html>
        <head>
            <title>Home</title>
        </head>
        <body>
            <h1>Selamat datang, {{ user.username }}!</h1>
        </body>
    </html>
    """

