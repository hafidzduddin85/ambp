# app/main.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.init import create_app
from app.config import load_config
from app.database.database import init_db
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load konfigurasi
config = load_config()

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    # Continue anyway for Google Sheets functionality

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
