# app/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.init import create_app
from app.config import load_config
from app.database.database import init_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load konfigurasi
config = load_config()

# Inisialisasi database (hanya jika pakai SQLAlchemy)
try:
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Database initialization failed: {e}")
    # Tidak hentikan program karena ada fallback ke Google Sheets

# Inisialisasi aplikasi FastAPI
app = create_app()

# Tambahkan session middleware
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET)

# Mount folder static
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Route favicon.ico
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join(static_path, "favicon.ico"))
