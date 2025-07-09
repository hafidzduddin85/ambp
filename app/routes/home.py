# app/routes/home.py
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/")
def root_redirect():
    return RedirectResponse(url="/home")
