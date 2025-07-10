# app/config.py
import os
import json
from typing import Dict

class Config:
    def __init__(self):
        self.GOOGLE_CREDS_JSON = self._load_google_creds()
        self.GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
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