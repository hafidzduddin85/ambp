import os
import json
import gspread
import logging
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from datetime import datetime
from google.oauth2.service_account import Credentials
from app.utils.cache import get_cached_data, clear_cache
from functools import wraps
import time

# ========================
# Koneksi & Autentikasi
# ========================
_sheet_cache = None
_worksheets_cache = {}

def retry_on_api_error(max_retries=3, backoff_factor=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (gspread.exceptions.APIError, ConnectionError, Exception) as e:
                    if attempt == max_retries - 1:
                        logging.error(f"API call failed after {max_retries} attempts: {e}")
                        raise
                    wait_time = backoff_factor * (2 ** attempt)
                    logging.warning(f"API call failed, retrying in {wait_time}s... ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

@retry_on_api_error(max_retries=3, backoff_factor=2)
def get_sheet():
    global _sheet_cache
    if _sheet_cache:
        try:
            _sheet_cache.get_worksheet_by_id(0)
            return _sheet_cache
        except:
            _sheet_cache = None
            clear_worksheet_cache()

    creds_json_str = os.getenv("GOOGLE_CREDS_JSON")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not creds_json_str or not sheet_id:
        logging.error("GOOGLE_CREDS_JSON dan/atau GOOGLE_SHEET_ID belum di-set di environment.")
        raise RuntimeError("Google Sheets credentials or sheet ID not set.")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = json.loads(creds_json_str)
    if "private_key" in creds_json:
        creds_json["private_key"] = creds_json["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)
    _sheet_cache = client.open_by_key(sheet_id)
    return _sheet_cache

@retry_on_api_error(max_retries=2)
def get_worksheet(name: str):
    if name not in _worksheets_cache:
        try:
            _worksheets_cache[name] = get_sheet().worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            logging.warning(f"Sheet '{name}' not found.")
            _worksheets_cache[name] = None
            return None
        except Exception as e:
            logging.error(f"Error accessing worksheet '{name}': {e}")
            return None
    return _worksheets_cache[name]

def clear_worksheet_cache():
    global _worksheets_cache
    _worksheets_cache.clear()

# ========================
# Referensi Dropdown Input
# ========================
def get_reference_lists() -> dict:
    return get_cached_data("reference_lists", _load_all_references)

@retry_on_api_error()
def _load_all_references() -> dict:
    ref_data = {"categories": [], "types": [], "companies": [], "owners": [], "locations": [], "rooms": []}
    try:
        sheet_names = ["Ref_Categories", "Ref_Types", "Ref_Companies", "Ref_Owners", "Ref_Location"]
        worksheets = {name: get_worksheet(name) for name in sheet_names}

        if worksheets["Ref_Categories"]:
            values = worksheets["Ref_Categories"].col_values(1)[1:]
            ref_data["categories"] = sorted({v.strip() for v in values if v.strip()})

        if worksheets["Ref_Types"]:
            ref_data["types"] = worksheets["Ref_Types"].get_all_records()

        if worksheets["Ref_Companies"]:
            records = worksheets["Ref_Companies"].get_all_records()
            ref_data["companies"] = [f"{r['Company']} ({r['Code Company']})" for r in records]

        if worksheets["Ref_Owners"]:
            values = worksheets["Ref_Owners"].col_values(1)[1:]
            ref_data["owners"] = sorted({v.strip() for v in values if v.strip()})

        if worksheets["Ref_Location"]:
            records = worksheets["Ref_Location"].get_all_records()
            locations, rooms = set(), set()
            for row in records:
                loc, room = row.get("Location", "").strip(), row.get("Room", "").strip()
                if loc: locations.add(loc)
                if room: rooms.add(room)
            ref_data["locations"] = sorted(locations)
            ref_data["rooms"] = sorted(rooms)

        return ref_data
    except Exception as e:
        logging.warning(f"Gagal load reference data: {e}")
        return ref_data

def get_location_room_map() -> dict:
    return get_cached_data("location_room_map", _build_location_room_map)

def _build_location_room_map() -> dict:
    try:
        ws = get_worksheet("Ref_Location")
        if not ws:
            return {}

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

# ========================
# Ambil Data Aset
# ========================
def get_assets(status_filter: str = "All") -> list:
    try:
        ws = get_worksheet("Assets")
        if not ws:
            return []
        data = ws.get_all_records()
        if status_filter != "All":
            return [row for row in data if row.get("Status", "").lower() == status_filter.lower()]
        return data
    except Exception as e:
        logging.warning(f"Gagal mengambil data aset: {e}")
        return []

# ========================
# Tambahkan Data Aset
# ========================
@retry_on_api_error()
def append_asset(data: dict):
    try:
        ws = get_worksheet("Assets")
        if not ws: return

        # Add asset with empty calculated fields
        row_data = [
            "", data.get("item_name", ""), data.get("category", ""), data.get("type", ""),
            data.get("manufacture", ""), data.get("model", ""), data.get("serial_number", ""),
            "", data.get("company", ""), data.get("bisnis_unit", ""),
            data.get("location", ""), data.get("room_location", ""), data.get("notes", "Input dari Web"),
            data.get("condition", ""), data.get("purchase_date", ""), data.get("purchase_cost", ""),
            data.get("warranty", "No"), data.get("supplier", ""), data.get("journal", ""),
            data.get("owner", ""), "", "", "", "", "", "Active", ""
        ]

        ws.append_row(row_data)
        
        # Auto-sync to fill calculated fields
        try:
            # Clear cache to ensure fresh reference data
            clear_cache()
            clear_worksheet_cache()
            
            sync_result = sync_assets_data()
            logging.info(f"Auto-sync after asset creation: {sync_result.get('message', 'completed')}")
        except Exception as sync_error:
            logging.warning(f"Auto-sync failed after asset creation: {sync_error}")
            
    except Exception as e:
        logging.warning(f"Gagal menambahkan data aset: {e}")

# ========================
# Sync Data Aset
# ========================
def to_decimal(value, default=Decimal(0)):
    try:
        return Decimal(str(value).replace(",", "").replace("Rp", "").strip())
    except (InvalidOperation, AttributeError, ValueError):
        return default

def to_int(value, default=1):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

@retry_on_api_error(max_retries=2)
def sync_assets_data():
    try:
        ref_data = get_cached_data("sync_references", _load_sync_references)
        assets_ws = get_worksheet("Assets")
        if not assets_ws: 
            return {"success": False, "message": "Assets worksheet not found"}

        headers = assets_ws.row_values(1)
        data = assets_ws.get_all_values()[1:]
        if not data:
            return {"success": True, "message": "No data to sync", "updated": 0}

        updated_data = []
        tracker = defaultdict(int)
        current_year = datetime.now().year
        header_map = {h: i for i, h in enumerate(headers)}

        for i, row in enumerate(data):
            row_dict = dict(zip(headers, row))
            updated_row = list(row)

            if "ID" in header_map:
                updated_row[header_map["ID"]] = str(i + 1).zfill(3)

            purchase_date = row_dict.get("Purchase Date", "")
            try:
                year = datetime.strptime(purchase_date, "%Y-%m-%d").year if purchase_date else current_year
            except:
                year = current_year

            if "Tahun" in header_map:
                updated_row[header_map["Tahun"]] = str(year)

            category = row_dict.get("Category", "")
            cat_ref = ref_data["categories"].get(category, {})

            residual_percent = to_decimal(cat_ref.get("Residual Percent", "0"))
            if "Residual Percent" in header_map:
                updated_row[header_map["Residual Percent"]] = str(residual_percent)

            useful_life = to_int(cat_ref.get("Useful Life", "1"))
            if "Useful Life" in header_map:
                updated_row[header_map["Useful Life"]] = str(useful_life)

            purchase_cost = to_decimal(row_dict.get("Purchase Cost", "0"))
            residual_value = (purchase_cost * residual_percent / 100).quantize(Decimal("0.01"))
            if "Residual Value" in header_map:
                updated_row[header_map["Residual Value"]] = str(residual_value)

            depreciation_value = ((purchase_cost - residual_value) / useful_life).quantize(Decimal("0.01")) if useful_life > 0 else Decimal(0)
            if "Depreciation Value" in header_map:
                updated_row[header_map["Depreciation Value"]] = str(depreciation_value)

            age = max(0, current_year - year)
            book_value = (purchase_cost - (depreciation_value * age)).quantize(Decimal("0.01"))
            if "Book Value" in header_map:
                updated_row[header_map["Book Value"]] = str(book_value)

            code_category = cat_ref.get("Code Category", "")
            if "Code Category" in header_map:
                updated_row[header_map["Code Category"]] = str(code_category).zfill(2) if code_category else ""

            company = row_dict.get("Company", "")
            code_company = ref_data["companies"].get(company, "")
            if "Code Company" in header_map:
                updated_row[header_map["Code Company"]] = code_company

            type_name = row_dict.get("Type", "")
            code_type = ref_data["types"].get((type_name, category), "")
            if "Code Type" in header_map:
                updated_row[header_map["Code Type"]] = str(code_type).zfill(2) if code_type else ""

            owner = row_dict.get("Owner", "")
            code_owner = ref_data["owners"].get(owner, "")
            if "Code Owner" in header_map:
                updated_row[header_map["Code Owner"]] = code_owner

            if code_company and code_category and code_type and code_owner:
                key = (code_company, code_type, str(year))
                tracker[key] += 1
                seq_num = str(tracker[key]).zfill(3)
                year_2digit = str(year)[-2:]
                asset_tag = f"{code_company}-{str(code_category).zfill(2)}{str(code_type).zfill(2)}.{code_owner}{year_2digit}.{seq_num}"
                if "Asset Tag" in header_map:
                    updated_row[header_map["Asset Tag"]] = asset_tag

            updated_data.append(updated_row)

        if updated_data:
            assets_ws.update([headers] + updated_data)
            return {"success": True, "message": f"Successfully synced {len(updated_data)} assets", "updated": len(updated_data)}

        return {"success": True, "message": "No data to update", "updated": 0}

    except Exception as e:
        logging.error(f"Sync error: {e}")
        return {"success": False, "message": f"Sync failed: {str(e)}", "updated": 0}

@retry_on_api_error()
def _load_sync_references() -> dict:
    ref_data = {"categories": {}, "types": {}, "companies": {}, "owners": {}}
    try:
        ws = get_worksheet("Ref_Categories")
        if ws:
            for row in ws.get_all_records():
                ref_data["categories"][row["Category"]] = {
                    "Code Category": row["Code Category"],
                    "Residual Percent": row["Residual Percent"],
                    "Useful Life": row["Useful Life"]
                }

        ws = get_worksheet("Ref_Types")
        if ws:
            for row in ws.get_all_records():
                ref_data["types"][(row["Type"], row["Category"])] = row["Code Type"]

        ws = get_worksheet("Ref_Companies")
        if ws:
            for row in ws.get_all_records():
                ref_data["companies"][row["Company"]] = row["Code Company"]

        ws = get_worksheet("Ref_Owners")
        if ws:
            for row in ws.get_all_records():
                ref_data["owners"][row["Owner"]] = row["Code Owner"]

        return ref_data
    except Exception as e:
        logging.warning(f"Failed to load sync references: {e}")
        return ref_data
