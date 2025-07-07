# app/sheets.py
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_json = json.loads(os.getenv("GOOGLE_CREDS_JSON", "{}"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)

    sheet_id = os.getenv("SHEET_ID")
    return client.open_by_key(sheet_id)

def append_asset(data: dict):
    sheet = get_sheet()
    ws = sheet.worksheet("Assets")
    ws.append_row([
        data.get("item_name", ""),
        data.get("category", ""),
        data.get("type", ""),
        data.get("company", ""),
        data.get("owner", ""),
        data.get("purchase_date", ""),
        data.get("purchase_cost", ""),
        "Input dari Web",  # Notes
    ])