import os
import json
import gspread
import logging
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from app.cache import get_cached_data, clear_cache

# ========================
# Koneksi & Autentikasi
# ========================
_sheet_cache = None

def get_sheet():
    """Koneksi ke Google Sheets dan cache instance"""
    global _sheet_cache
    if _sheet_cache:
        return _sheet_cache

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = json.loads(os.getenv("GOOGLE_CREDS_JSON", "{}"))
    if "private_key" in creds_json:
        creds_json["private_key"] = creds_json["private_key"].replace("\\n", "\n")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    _sheet_cache = client.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
    return _sheet_cache

# ========================
# Referensi Dropdown Input
# ========================
def get_reference_lists() -> dict:
    """Ambil semua referensi untuk form input (cache 5 menit)"""
    return get_cached_data("reference_lists", lambda: {
        "categories": get_ref_column("Ref_Categories", 1),
        "types": get_ref_types(),
        "companies": get_ref_companies(),
        "owners": get_ref_column("Ref_Owners", 1),
        "locations": get_ref_column("Ref_Location", 1),
        "rooms": get_ref_column("Ref_Location", 2)
    })

def get_location_room_map() -> dict:
    """Mapping lokasi → list ruangan"""
    return get_cached_data("location_room_map", _build_location_room_map)

def _build_location_room_map() -> dict:
    try:
        ws = get_sheet().worksheet("Ref_Location")
        mapping = {}
        for row in ws.get_all_records():
            location = row.get("Location", "").strip()
            room = row.get("Room", "").strip()
            if location:
                mapping.setdefault(location, []).append(room)
        return mapping
    except Exception as e:
        logging.warning(f"Gagal ambil lokasi & ruangan: {e}")
        return {}

def get_ref_column(sheet_name: str, col: int) -> list:
    try:
        ws = get_sheet().worksheet(sheet_name)
        values = ws.col_values(col)[1:]
        return sorted(set(v.strip() for v in values if v.strip()))
    except gspread.exceptions.WorksheetNotFound:
        logging.warning(f"Sheet '{sheet_name}' not found.")
        return []

def get_ref_types() -> list:
    try:
        return get_sheet().worksheet("Ref_Types").get_all_records()
    except gspread.exceptions.WorksheetNotFound:
        logging.warning("Sheet 'Ref_Types' not found.")
        return []

def get_ref_companies() -> list:
    try:
        records = get_sheet().worksheet("Ref_Companies").get_all_records()
        return [f"{r['Company']} ({r['Code Company']})" for r in records]
    except gspread.exceptions.WorksheetNotFound:
        logging.warning("Sheet 'Ref_Companies' not found.")
        return []

# ================================
# Tambah Referensi Jika Belum Ada
# ================================
def add_type_if_not_exists(type_name: str, category: str):
    try:
        ws = get_sheet().worksheet("Ref_Types")
        existing = ws.get_all_records()
        if not any(r["Type"].strip().lower() == type_name.strip().lower()
                   and r["Category"].strip().lower() == category.strip().lower() for r in existing):
            next_code = str(len(existing) + 1).zfill(2)
            ws.append_row([type_name, category, next_code])
            clear_cache("reference_lists")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Type '{type_name}': {e}")

def add_category_if_not_exists(category_name: str):
    try:
        ws = get_sheet().worksheet("Ref_Categories")
        existing = [c.strip().lower() for c in ws.col_values(1)[1:]]
        if category_name.strip().lower() not in existing:
            ws.append_row([category_name, "100", "5"])
            clear_cache("reference_lists")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Category '{category_name}': {e}")

def add_company_with_code_if_not_exists(company: str, code_company: str):
    try:
        ws = get_sheet().worksheet("Ref_Companies")
        records = ws.get_all_records()
        companies = [r["Company"].strip().lower() for r in records]
        codes = [r["Code Company"].strip().upper() for r in records]
        if company.strip().lower() not in companies:
            if code_company.strip().upper() in codes:
                raise ValueError("Code Company sudah digunakan")
            ws.append_row([company, code_company])
            clear_cache("reference_lists")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Company '{company}': {e}")

def add_owner_if_not_exists(owner_name: str):
    try:
        ws = get_sheet().worksheet("Ref_Owners")
        owners = [o.strip().lower() for o in ws.col_values(1)[1:]]
        if owner_name.strip().lower() not in owners:
            next_code = str(len(owners) + 1).zfill(2)
            ws.append_row([owner_name, next_code])
            clear_cache("reference_lists")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Owner '{owner_name}': {e}")

def add_location_if_not_exists(location: str, room: str):
    try:
        ws = get_sheet().worksheet("Ref_Location")
        records = ws.get_all_records()
        if not any(r["Location"].strip().lower() == location.strip().lower()
                   and r["Room"].strip().lower() == room.strip().lower() for r in records):
            ws.append_row([location, room])
            clear_cache("reference_lists")
            clear_cache("location_room_map")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Lokasi '{location} - {room}': {e}")

# ========================
# Ambil Data Aset
# ========================
def get_assets(status_filter: str = "All") -> list:
    data = get_sheet().worksheet("Assets").get_all_records()
    if status_filter != "All":
        return [row for row in data if row.get("Status", "").lower() == status_filter.lower()]
    return data

# ========================
# ID & Tag Generator
# ========================
def get_next_asset_id() -> str:
    ids = get_sheet().worksheet("Assets").col_values(1)
    angka_terakhir = max(
        (int(i[1:]) for i in ids[1:] if i.startswith("A") and i[1:].isdigit()),
        default=0
    )
    return f"A{str(angka_terakhir + 1).zfill(3)}"

def generate_asset_tag(code_company: str, category: str, type_: str, owner: str) -> str:
    sheet = get_sheet()
    ref_categories = sheet.worksheet("Ref_Categories").get_all_records()
    ref_types = sheet.worksheet("Ref_Types").get_all_records()
    ref_owners = sheet.worksheet("Ref_Owners").get_all_records()
    assets = sheet.worksheet("Assets").get_all_records()

    code_category = next((r["Code Category"] for r in ref_categories if r["Category"] == category), "XX")
    code_type = next((r["Code Type"] for r in ref_types if r["Type"] == type_ and r["Category"] == category), "XX")
    code_owner = next((r["Code Owner"] for r in ref_owners if r["Owner"] == owner), "XX")
    tahun = datetime.now().year

    count = sum(
        1 for a in assets
        if a.get("Company") and a.get("Type") == type_ and str(a.get("Tahun")) == str(tahun)
    ) + 1

    no_urut = str(count).zfill(4)
    return f"{code_company}-{code_category}{code_type}.{code_owner}{tahun}.{no_urut}"

# ========================
# Tambahkan Data Aset
# ========================
def append_asset(data: dict):
    ws = get_sheet().worksheet("Assets")
    asset_id = get_next_asset_id()
    asset_tag = generate_asset_tag(
        code_company=data["code_company"],
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
