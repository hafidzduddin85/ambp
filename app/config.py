# === config.py ===
import os
import json
from dotenv import load_dotenv
from typing import Dict
from dataclasses import dataclass

load_dotenv()

@dataclass
class Config:
    """
    Konfigurasi bot yang diambil dari environment variable atau file .env
    """
    DATABASE_URL: str
    GOOGLE_SHEET_ID: str
    GOOGLE_CREDS_JSON: Dict
    SESSION_SECRET: str

def load_config() -> Config:
    # Ambil variabel lingkungan
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("❌ DATABASE_URL environment variable must be set and non-empty.")

    session_secret = os.getenv("SESSION_SECRET")
    if not session_secret:
        raise ValueError("❌ SESSION_SECRET environment variable must be set and non-empty.")

    google_sheet_id = os.getenv("GOOGLE_SHEET_ID", "")

    creds_env = os.getenv("GOOGLE_CREDS_JSON", "")
    try:
        google_creds_json = json.loads(creds_env) if creds_env else {}
    except Exception as e:
        print(f"❌ Gagal parse GOOGLE_CREDS_JSON: {e}")
        google_creds_json = {}

    # Buat instance Config
    return Config(
        DATABASE_URL=database_url,
        GOOGLE_SHEET_ID=google_sheet_id,
        GOOGLE_CREDS_JSON=google_creds_json,
        SESSION_SECRET=session_secret
    )
