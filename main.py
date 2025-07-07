# app/main.py
from fastapi import FastAPI
from app.sheets import get_sheet

app = FastAPI()

@app.get("/")
def read_root():
    sheet = get_sheet()
    assets = sheet.worksheet("Assets").get_all_records()
    return {"total_assets": len(assets)}
