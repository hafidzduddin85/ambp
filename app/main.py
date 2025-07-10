# app/main.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.init import create_app
from app.config import load_config

# Load konfigurasi
config = load_config()

# Inisialisasi FastAPI
app = create_app()
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET)

# Mount folder static
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Handle favicon
@app.get("/favicon.ico")
def favicon():
    return FileResponse(os.path.join(static_path, "favicon.ico"))
