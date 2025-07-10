import os
import json
import gspread
import logging
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from app.cache import get_cached_data, clear_cache
from functools import wraps
import time

# ========================
# Koneksi & Autentikasi
# ========================
_sheet_cache = None
_worksheets_cache = {}

def retry_on_api_error(max_retries=3, backoff_factor=1):
    """Decorator for retrying API calls with exponential backoff"""
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
    """Koneksi ke Google Sheets dan cache instance"""
    global _sheet_cache
    if _sheet_cache:
        try:
            # Test connection
            _sheet_cache.get_worksheet_by_id(0)
            return _sheet_cache
        except:
            # Reset cache if connection is stale
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
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    _sheet_cache = client.open_by_key(sheet_id)
    return _sheet_cache

@retry_on_api_error(max_retries=2)
def get_worksheet(name: str):
    """Get worksheet with caching and error handling"""
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
    """Clear worksheet cache"""
    global _worksheets_cache
    _worksheets_cache.clear()

# ========================
# Referensi Dropdown Input
# ========================
def get_reference_lists() -> dict:
    """Ambil semua referensi untuk form input (cache 5 menit)"""
    return get_cached_data("reference_lists", _load_all_references)

@retry_on_api_error()
def _load_all_references() -> dict:
    """Load all reference data in single batch"""
    ref_data = {"categories": [], "types": [], "companies": [], "owners": [], "locations": [], "rooms": []}
    
    try:
        # Batch load all worksheets at once
        sheet_names = ["Ref_Categories", "Ref_Types", "Ref_Companies", "Ref_Owners", "Ref_Location"]
        worksheets = {name: get_worksheet(name) for name in sheet_names}
        
        # Load categories
        if worksheets["Ref_Categories"]:
            values = worksheets["Ref_Categories"].col_values(1)[1:]
            ref_data["categories"] = sorted({v.strip() for v in values if v.strip()})
        
        # Load types
        if worksheets["Ref_Types"]:
            ref_data["types"] = worksheets["Ref_Types"].get_all_records()
        
        # Load companies
        if worksheets["Ref_Companies"]:
            records = worksheets["Ref_Companies"].get_all_records()
            ref_data["companies"] = [f"{r['Company']} ({r['Code Company']})" for r in records]
        
        # Load owners
        if worksheets["Ref_Owners"]:
            values = worksheets["Ref_Owners"].col_values(1)[1:]
            ref_data["owners"] = sorted({v.strip() for v in values if v.strip()})
        
        # Load locations and rooms
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
    """Mapping lokasi → list ruangan"""
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

# ================================
# Tambah Referensi Jika Belum Ada
# ================================
@retry_on_api_error()
def add_reference_batch(additions: list):
    """Add multiple references in batch"""
    try:
        for addition in additions:
            sheet_name, data = addition["sheet"], addition["data"]
            ws = get_worksheet(sheet_name)
            if ws:
                ws.append_row(data)
        
        # Clear all reference caches
        for cache_key in ["reference_lists", "location_room_map", "tag_references", "sync_references"]:
            clear_cache(cache_key)
    except Exception as e:
        logging.warning(f"Gagal batch add references: {e}")

def add_type_if_not_exists(type_name: str, category: str):
    try:
        ws = get_worksheet("Ref_Types")
        if not ws: return
        
        existing = ws.get_all_records()
        if not any(r["Type"].strip().lower() == type_name.strip().lower()
                   and r["Category"].strip().lower() == category.strip().lower() for r in existing):
            ws.append_row([type_name, category, str(len(existing) + 1).zfill(2)])
            clear_cache("reference_lists")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Type '{type_name}': {e}")

def add_category_if_not_exists(category_name: str):
    try:
        ws = get_worksheet("Ref_Categories")
        if not ws: return
        
        existing = {c.strip().lower() for c in ws.col_values(1)[1:]}
        if category_name.strip().lower() not in existing:
            ws.append_row([category_name, "100", "5"])
            clear_cache("reference_lists")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Category '{category_name}': {e}")

def add_company_with_code_if_not_exists(company: str, code_company: str):
    try:
        ws = get_worksheet("Ref_Companies")
        if not ws: return
        
        records = ws.get_all_records()
        companies = {r["Company"].strip().lower() for r in records}
        codes = {r["Code Company"].strip().upper() for r in records}
        
        if company.strip().lower() not in companies:
            if code_company.strip().upper() in codes:
                raise ValueError("Code Company sudah digunakan")
            ws.append_row([company, code_company])
            clear_cache("reference_lists")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Company '{company}': {e}")

def add_owner_if_not_exists(owner_name: str):
    try:
        ws = get_worksheet("Ref_Owners")
        if not ws: return
        
        values = ws.col_values(1)[1:]
        owners = {o.strip().lower() for o in values if o.strip()}
        if owner_name.strip().lower() not in owners:
            next_code = str(len(values) + 1).zfill(2)
            ws.append_row([owner_name, next_code])
            clear_cache("reference_lists")
    except Exception as e:
        logging.warning(f"Gagal menambahkan Owner '{owner_name}': {e}")

def add_location_if_not_exists(location: str, room: str):
    try:
        ws = get_worksheet("Ref_Location")
        if not ws: return
        
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
    except Exception as e:
        logging.warning(f"Gagal menambahkan data aset: {e}")

@retry_on_api_error()
def append_assets_batch(assets_data: list):
    """Add multiple assets in batch"""
    try:
        ws = get_worksheet("Assets")
        if not ws: return
        
        rows_to_add = []
        for data in assets_data:
            row_data = [
                "", data.get("item_name", ""), data.get("category", ""), data.get("type", ""),
                data.get("manufacture", ""), data.get("model", ""), data.get("serial_number", ""),
                "", data.get("company", ""), data.get("bisnis_unit", ""),
                data.get("location", ""), data.get("room_location", ""), data.get("notes", "Input dari Web"),
                data.get("condition", ""), data.get("purchase_date", ""), data.get("purchase_cost", ""),
                data.get("warranty", "No"), data.get("supplier", ""), data.get("journal", ""),
                data.get("owner", ""), "", "", "", "", "", "Active", ""
            ]
            rows_to_add.append(row_data)
        
        # Batch insert all rows at once
        if rows_to_add:
            ws.append_rows(rows_to_add)
    except Exception as e:
        logging.warning(f"Gagal batch add assets: {e}")

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
        # Load reference data
        ref_data = get_cached_data("sync_references", _load_sync_references)
        assets_ws = get_worksheet("Assets")
        if not assets_ws: 
            return {"success": False, "message": "Assets worksheet not found"}
        
        # Get all data
        headers = assets_ws.row_values(1)
        data = assets_ws.get_all_values()[1:]
        
        if not data:
            return {"success": True, "message": "No data to sync", "updated": 0}
            
        updated_data = []
        tracker = defaultdict(int)
        current_year = datetime.now().year
        
        # Pre-calculate header indices
        header_map = {h: i for i, h in enumerate(headers)}
        
        for i, row in enumerate(data):
            row_dict = dict(zip(headers, row))
            updated_row = list(row)
            
            # 1. ID - Sequential number
            if "ID" in header_map:
                updated_row[header_map["ID"]] = str(i + 1)
            
            # 2. Tahun - Extract from Purchase Date
            purchase_date = row_dict.get("Purchase Date", "")
            try:
                year = datetime.strptime(purchase_date, "%Y-%m-%d").year if purchase_date else current_year
            except:
                year = current_year
            
            if "Tahun" in header_map:
                updated_row[header_map["Tahun"]] = str(year)
            
            # 3. Get reference data based on category
            category = row_dict.get("Category", "")
            cat_ref = ref_data["categories"].get(category, {})
            
            # 4. Residual Percent from Ref_Categories
            residual_percent = to_decimal(cat_ref.get("Residual Percent", "0"))
            if "Residual Percent" in header_map:
                updated_row[header_map["Residual Percent"]] = str(residual_percent)
            
            # 5. Useful Life from Ref_Categories
            useful_life = to_int(cat_ref.get("Useful Life", "1"))
            if "Useful Life" in header_map:
                updated_row[header_map["Useful Life"]] = str(useful_life)
            
            # 6. Calculate financial values
            purchase_cost = to_decimal(row_dict.get("Purchase Cost", "0"))
            
            # Residual Value = Residual Percent × Purchase Cost
            residual_value = (purchase_cost * residual_percent / 100).quantize(Decimal("0.01"))
            if "Residual Value" in header_map:
                updated_row[header_map["Residual Value"]] = str(residual_value)
            
            # Depreciation Value = (Purchase Cost - Residual Value) / Useful Life
            depreciation_value = ((purchase_cost - residual_value) / useful_life).quantize(Decimal("0.01")) if useful_life > 0 else Decimal(0)
            if "Depreciation Value" in header_map:
                updated_row[header_map["Depreciation Value"]] = str(depreciation_value)
            
            # Book Value = Purchase Cost - (Depreciation Value × (Current Year - Asset Year))
            age = max(0, current_year - year)
            book_value = (purchase_cost - (depreciation_value * age)).quantize(Decimal("0.01"))
            if "Book Value" in header_map:
                updated_row[header_map["Book Value"]] = str(book_value)
            
            # 7. Code Category from Ref_Categories
            code_category = cat_ref.get("Code Category", "")
            if "Code Category" in header_map:
                updated_row[header_map["Code Category"]] = code_category
            
            # 8. Code Company from Ref_Companies
            company = row_dict.get("Company", "")
            code_company = ref_data["companies"].get(company, "")
            if "Code Company" in header_map:
                updated_row[header_map["Code Company"]] = code_company
            
            # 9. Code Type from Ref_Types
            type_name = row_dict.get("Type", "")
            code_type = ref_data["types"].get((type_name, category), "")
            if "Code Type" in header_map:
                updated_row[header_map["Code Type"]] = code_type
            
            # 10. Code Owner from Ref_Owners
            owner = row_dict.get("Owner", "")
            code_owner = ref_data["owners"].get(owner, "")
            if "Code Owner" in header_map:
                updated_row[header_map["Code Owner"]] = code_owner
            
            # 11. Asset Tag: [Code Company]-[Code Category][Code Type].[Code Owner][2 digit year].[Sequential number]
            if code_company and code_category and code_type and code_owner:
                key = (code_company, code_type, str(year))
                tracker[key] += 1
                seq_num = str(tracker[key]).zfill(3)
                year_2digit = str(year)[-2:]
                asset_tag = f"{code_company}-{code_category}{code_type}.{code_owner}{year_2digit}.{seq_num}"
                
                if "Asset Tag" in header_map:
                    updated_row[header_map["Asset Tag"]] = asset_tag
            
            updated_data.append(updated_row)
        
        # Update the sheet
        if updated_data:
            assets_ws.update([headers] + updated_data)
            return {"success": True, "message": f"Successfully synced {len(updated_data)} assets", "updated": len(updated_data)}
        
        return {"success": True, "message": "No data to update", "updated": 0}
        
    except Exception as e:
        logging.error(f"Sync error: {e}")
        return {"success": False, "message": f"Sync failed: {str(e)}", "updated": 0}

@retry_on_api_error()
def _load_sync_references() -> dict:
    """Load all reference data for sync operation"""
    ref_data = {"categories": {}, "types": {}, "companies": {}, "owners": {}}
    
    try:
        # Load Ref_Categories
        ws = get_worksheet("Ref_Categories")
        if ws:
            for row in ws.get_all_records():
                ref_data["categories"][row["Category"]] = {
                    "Code Category": row["Code Category"],
                    "Residual Percent": row["Residual Percent"],
                    "Useful Life": row["Useful Life"]
                }
        
        # Load Ref_Types
        ws = get_worksheet("Ref_Types")
        if ws:
            for row in ws.get_all_records():
                ref_data["types"][(row["Type"], row["Category"])] = row["Code Type"]
        
        # Load Ref_Companies
        ws = get_worksheet("Ref_Companies")
        if ws:
            for row in ws.get_all_records():
                ref_data["companies"][row["Company"]] = row["Code Company"]
        
        # Load Ref_Owners
        ws = get_worksheet("Ref_Owners")
        if ws:
            for row in ws.get_all_records():
                ref_data["owners"][row["Owner"]] = row["Code Owner"]
        
        return ref_data
    except Exception as e:
        logging.warning(f"Failed to load sync references: {e}")
        return ref_data