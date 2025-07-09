# app/utils.py

from starlette.requests import Request

def set_flash(request: Request, message: str):
    request.session["flash"] = message

def get_flash(request: Request):
    return request.session.pop("flash", None)