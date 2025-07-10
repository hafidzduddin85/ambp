# app/config.py
import os
import json
from typing import Dict

class Config:
    def __init__(self):
        self._creds = self._load_google_creds()

    @property
    def GOOGLE_CREDS_JSON(self) -> Dict:
        return self._creds

    @property
    def GOOGLE_SHEET_ID(self) -> str:
        return os.getenv("GOOGLE_SHEET_ID", "")

    @property
    def SESSION_SECRET(self) -> str:
        secret = os.getenv("SESSION_SECRET")
        if not secret:
            raise RuntimeError("SESSION_SECRET is not set in environment")
        return secret
    
    @property
    def DATABASE_URL(self) -> str:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL is not set in environment")
        # Fix PostgreSQL URL format if needed (Render.com compatibility)
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return db_url

    def _load_google_creds(self) -> Dict:
        creds_json_str = os.getenv("GOOGLE_CREDS_JSON")
        if not creds_json_str:
            raise RuntimeError("GOOGLE_CREDS_JSON not set in environment")

        creds_json = json.loads(creds_json_str)
        if "private_key" in creds_json:
            creds_json["private_key"] = creds_json["private_key"].replace("\\n", "\n")
        return creds_json

def load_config() -> Config:
    return Config()
