# app/utils/flash.py

from starlette.requests import Request

def set_flash(request: Request, message: str, category: str = "info"):
    request.session["_flash"] = {"message": message, "category": category}

def get_flash(request: Request):
    return request.session.pop("_flash", None)