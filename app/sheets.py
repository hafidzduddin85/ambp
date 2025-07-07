import os
import json
import gspread
import logging
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ========================
# Koneksi & Autentikasi
# ========================
def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_json = json.loads(os.getenv("GOOGLE_CREDS_JSON", "{}"))
    if "private_key" in creds_json:
        creds_json["private_key"] = creds_json["private_key"].replace("\\n", "\n")

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id)

# ========================
# Referensi Dropdown Input
# ========================
def get_reference_lists() -> dict:
    sheet = get_sheet()
    refs = {}

    try:
        refs["categories"] = sheet.worksheet("Ref_Categories").col_values(1)[1:]
    except gspread.exceptions.WorksheetNotFound:
        logging.warning("Sheet 'Ref_Categories' not found.")
        refs["categories"] = []

    try:
        ws = sheet.worksheet("Ref_Types")
        rows = ws.get_all_values()[1:]  # Skip header
        refs["types"] = {}
        for row in rows:
            if len(row) >= 2:
                type_name = row[0]
                category = row[1]
                if category not in refs["types"]:
                    refs["types"][category] = []
                refs["types"][category].append(type_name)
    except gspread.exceptions.WorksheetNotFound:
        logging.warning("Sheet 'Ref_Types' not found.")
        refs["types"] = {}

    try:
        refs["companies"] = sheet.worksheet("Ref_Companies").col_values(1)[1:]
    except gspread.exceptions.WorksheetNotFound:
        logging.warning("Sheet 'Ref_Companies' not found.")
        refs["companies"] = []

    try:
        refs["owners"] = sheet.worksheet("Ref_Owners").col_values(1)[1:]
    except gspread.exceptions.WorksheetNotFound:
        logging.warning("Sheet 'Ref_Owners' not found.")
        refs["owners"] = []

    return refs

# ========================
# Ambil Data Aset
# ========================
def get_assets(status_filter: str = "All") -> list:
    sheet = get_sheet()
    data = sheet.worksheet("Assets").get_all_records()
    if status_filter != "All":
        return [row for row in data if row.get("Status", "").lower() == status_filter.lower()]
    return data

# ========================
# ID & Tag Generator
# ========================
def get_next_asset_id() -> str:
    sheet = get_sheet()
    ws = sheet.worksheet("Assets")
    ids = ws.col_values(1)  # kolom A = ID

    angka_terakhir = 0
    for id_val in ids[1:]:  # skip header
        if id_val.startswith("A") and id_val[1:].isdigit():
            angka = int(id_val[1:])
            angka_terakhir = max(angka_terakhir, angka)

    next_id = angka_terakhir + 1
    return f"A{str(next_id).zfill(3)}"

def generate_asset_tag(company: str, category: str, type_: str, owner: str) -> str:
    sheet = get_sheet()
    
    ref_companies = sheet.worksheet("Ref_Companies").get_all_records()
    ref_categories = sheet.worksheet("Ref_Categories").get_all_records()
    ref_types = sheet.worksheet("Ref_Types").get_all_records()
    ref_owners = sheet.worksheet("Ref_Owners").get_all_records()
    assets = sheet.worksheet("Assets").get_all_records()

    code_company = next((r["Code Company"] for r in ref_companies if r["Company"] == company), "XXX")
    code_category = next((r["Code Category"] for r in ref_categories if r["Category"] == category), "XXX")
    code_type = next((r["Code Type"] for r in ref_types if r["Type"] == type_ and r["Category"] == category), "XXX")
    code_owner = next((r["Code Owner"] for r in ref_owners if r["Owner"] == owner), "XXX")
    tahun = datetime.now().year

    count = 1
    for a in assets:
        if a["Company"] == company and a["Type"] == type_ and str(a["Tahun"]) == str(tahun):
            count += 1

    no_urut = str(count).zfill(4)
    return f"{code_company}-{code_category}{code_type}.{code_owner}{tahun}.{no_urut}"

# ========================
# Tambahkan Data Aset
# ========================
def append_asset(data: dict):
    sheet = get_sheet()
    ws = sheet.worksheet("Assets")

    asset_id = get_next_asset_id()
    asset_tag = generate_asset_tag(
        company=data["company"],
        category=data["category"],
        type_=data["type"],
        owner=data["owner"]
    )

    tahun = datetime.now().year

    ws.append_row([
        asset_id,  # ID
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
        "", "", "", "", "",  # Depreciation, Residual %, Residual Value, Useful Life, Book Value
        "Active",
        tahun
    ])
