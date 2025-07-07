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

    refs["categories"] = get_ref_column("Ref_Categories", 1)
    refs["types"] = get_ref_types()
    refs["companies"] = get_ref_column("Ref_Companies", 1)
    refs["owners"] = get_ref_column("Ref_Owners", 1)

    return refs

def get_ref_column(sheet_name: str, col: int) -> list:
    try:
        ws = get_sheet().worksheet(sheet_name)
        return ws.col_values(col)[1:]
    except gspread.exceptions.WorksheetNotFound:
        logging.warning(f"Sheet '{sheet_name}' not found.")
        return []

def get_ref_types() -> list:
    try:
        ws = get_sheet().worksheet("Ref_Types")
        return ws.get_all_records()
    except gspread.exceptions.WorksheetNotFound:
        logging.warning("Sheet 'Ref_Types' not found.")
        return []

# ================================
# Tambah ke Sheet Referensi Jika Belum Ada
# ================================
def add_type_if_not_exists(type_name: str, category: str):
    sheet = get_sheet()
    try:
        ws = sheet.worksheet("Ref_Types")
        types = ws.col_values(1)[1:]
        if type_name not in types:
            next_code = str(len(types) + 1).zfill(2)
            ws.append_row([type_name, category, next_code])
    except Exception as e:
        logging.warning(f"Gagal menambahkan Type '{type_name}': {e}")

def add_category_if_not_exists(category_name: str):
    sheet = get_sheet()
    try:
        ws = sheet.worksheet("Ref_Categories")
        categories = ws.col_values(1)[1:]
        if category_name not in categories:
            ws.append_row([category_name, "100", "5"])
    except Exception as e:
        logging.warning(f"Gagal menambahkan Category '{category_name}': {e}")

def add_company_if_not_exists(company_name: str):
    sheet = get_sheet()
    try:
        ws = sheet.worksheet("Ref_Companies")
        companies = ws.col_values(1)[1:]
        if company_name not in companies:
            next_code = str(len(companies) + 1).zfill(2)
            ws.append_row([company_name, next_code])
    except Exception as e:
        logging.warning(f"Gagal menambahkan Company '{company_name}': {e}")

def add_owner_if_not_exists(owner_name: str):
    sheet = get_sheet()
    try:
        ws = sheet.worksheet("Ref_Owners")
        owners = ws.col_values(1)[1:]
        if owner_name not in owners:
            next_code = str(len(owners) + 1).zfill(2)
            ws.append_row([owner_name, next_code])
    except Exception as e:
        logging.warning(f"Gagal menambahkan Owner '{owner_name}': {e}")

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
    ids = ws.col_values(1)

    angka_terakhir = 0
    for id_val in ids[1:]:
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
        asset_id,
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
        "", "", "", "", "",
        "Active",
        tahun
    ])
