# app/sheets.py
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
    
from datetime import datetime

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

def generate_asset_tag(company: str, category: str, type_: str, owner: str) -> str:
    sheet = get_sheet()
    
    # Ambil referensi
    ref_companies = sheet.worksheet("Ref_Companies").get_all_records()
    ref_categories = sheet.worksheet("Ref_Categories").get_all_records()
    ref_types = sheet.worksheet("Ref_Types").get_all_records()
    ref_owners = sheet.worksheet("Ref_Owners").get_all_records()
    assets = sheet.worksheet("Assets").get_all_records()

    # Mapping Code
    code_company = next((r["Code Company"] for r in ref_companies if r["Company"] == company), "XXX")
    code_category = next((r["Code Category"] for r in ref_categories if r["Category"] == category), "XXX")
    code_type = next((r["Code Type"] for r in ref_types if r["Type"] == type_ and r["Category"] == category), "XXX")
    code_owner = next((r["Code Owner"] for r in ref_owners if r["Owner"] == owner), "XXX")
    tahun = datetime.now().year

    # Hitung no urut berdasarkan kombinasi
    count = 1
    for a in assets:
        if a["Company"] == company and a["Type"] == type_ and str(a["Tahun"]) == str(tahun):
            count += 1

    no_urut = str(count).zfill(4)  # misal 0003
    kode = f"{code_company}-{code_category}{code_type}.{code_owner}{tahun}.{no_urut}"
    return kode

def append_asset(data: dict):
    sheet = get_sheet()
    ws = sheet.worksheet("Assets")

    asset_tag = generate_asset_tag(
        company=data["company"],
        category=data["category"],
        type_=data["type"],
        owner=data["owner"]
    )

    tahun = datetime.now().year

    ws.append_row([
        "",  # ID (biarkan kosong, bisa auto-generate pakai script terpisah)
        data.get("item_name", ""),
        data.get("category", ""),
        data.get("type", ""),
        data.get("manufacture", ""),
        data.get("model", ""),
        data.get("serial_number", ""),
        asset_tag,
        data.get("company", ""),
        data.get("bisnis_unit", ""),
        data.get("location", ""),
        data.get("room_location", ""),
        data.get("notes", "Input dari Web"),
        data.get("condition", ""),
        data.get("purchase_date", ""),
        data.get("purchase_cost", ""),
        data.get("warranty", "No"),
        data.get("supplier", ""),
        data.get("journal", ""),
        data.get("owner", ""),
        "",  # Depreciation Value
        "",  # Residual Percent
        "",  # Residual Value
        "",  # Useful Life
        "",  # Book Value
        "Active",
        tahun
    ])