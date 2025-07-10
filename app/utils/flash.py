# app/utils/flash.py
from fastapi import Request

def flash(request: Request, message: str, category: str = "info"):
    """Add flash message to session"""
    if "flash_messages" not in request.session:
        request.session["flash_messages"] = []
    request.session["flash_messages"].append({"message": message, "category": category})

def get_flashed_messages(request: Request):
    """Get and clear flash messages from session"""
    messages = request.session.get("flash_messages", [])
    if messages:
        request.session["flash_messages"] = []
    return messages