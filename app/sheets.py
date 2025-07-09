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
# ID & Tag Generator
# ========================
def get_next_asset_id() -> str:
    try:
        ws = get_worksheet("Assets")
        if not ws:
            return "A001"
        
        ids = ws.col_values(1)
        angka_terakhir = max(
            (int(i[1:]) for i in ids[1:] if i.startswith("A") and i[1:].isdigit()),
            default=0
        )
        return f"A{str(angka_terakhir + 1).zfill(3)}"
    except Exception as e:
        logging.warning(f"Gagal generate asset ID: {e}")
        return "A001"

@retry_on_api_error()
def generate_asset_tag(code_company: str, category: str, type_: str, owner: str) -> str:
    try:
        ref_data = get_cached_data("tag_references", _load_tag_references)
        
        code_category = ref_data["categories"].get(category, "XX")
        code_type = ref_data["types"].get((type_, category), "XX")
        code_owner = ref_data["owners"].get(owner, "XX")
        tahun = datetime.now().year

        # Count existing assets for this type and year
        assets = get_worksheet("Assets")
        count = 1
        if assets:
            count = sum(
                1 for a in assets.get_all_records()
                if a.get("Company") and a.get("Type") == type_ and str(a.get("Tahun")) == str(tahun)
            ) + 1

        no_urut = str(count).zfill(4)
        return f"{code_company}-{code_category}{code_type}.{code_owner}{tahun}.{no_urut}"
    except Exception as e:
        logging.warning(f"Gagal generate asset tag: {e}")
        return "TAG-ERROR"

@retry_on_api_error()
def _load_tag_references() -> dict:
    """Load reference data for tag generation"""
    ref_data = {"categories": {}, "types": {}, "owners": {}}
    
    try:
        worksheets = {
            "categories": get_worksheet("Ref_Categories"),
            "types": get_worksheet("Ref_Types"),
            "owners": get_worksheet("Ref_Owners")
        }
        
        if worksheets["categories"]:
            for r in worksheets["categories"].get_all_records():
                ref_data["categories"][r["Category"]] = r["Code Category"]
        
        if worksheets["types"]:
            for r in worksheets["types"].get_all_records():
                ref_data["types"][(r["Type"], r["Category"])] = r["Code Type"]
        
        if worksheets["owners"]:
            for r in worksheets["owners"].get_all_records():
                ref_data["owners"][r["Owner"]] = r["Code Owner"]
        
        return ref_data
    except Exception as e:
        logging.warning(f"Gagal load tag references: {e}")
        return ref_data

# ========================
# Tambahkan Data Aset
# ========================
@retry_on_api_error()
def append_asset(data: dict):
    try:
        ws = get_worksheet("Assets")
        if not ws: return
        
        asset_id = get_next_asset_id()
        asset_tag = generate_asset_tag(
            code_company=data["code_company"],
            category=data["category"],
            type_=data["type"],
            owner=data["owner"]
        )
        tahun = datetime.now().year

        row_data = [
            asset_id, data.get("item_name", ""), data.get("category", ""), data.get("type", ""),
            data.get("manufacture", ""), data.get("model", ""), data.get("serial_number", ""),
            asset_tag, data.get("company", ""), data.get("bisnis_unit", ""),
            data.get("location", ""), data.get("room_location", ""), data.get("notes", "Input dari Web"),
            data.get("condition", ""), data.get("purchase_date", ""), data.get("purchase_cost", ""),
            data.get("warranty", "No"), data.get("supplier", ""), data.get("journal", ""),
            data.get("owner", ""), "", "", "", "", "", "Active", tahun
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
            asset_id = get_next_asset_id()
            asset_tag = generate_asset_tag(
                code_company=data["code_company"],
                category=data["category"],
                type_=data["type"],
                owner=data["owner"]
            )
            tahun = datetime.now().year
            
            row_data = [
                asset_id, data.get("item_name", ""), data.get("category", ""), data.get("type", ""),
                data.get("manufacture", ""), data.get("model", ""), data.get("serial_number", ""),
                asset_tag, data.get("company", ""), data.get("bisnis_unit", ""),
                data.get("location", ""), data.get("room_location", ""), data.get("notes", "Input dari Web"),
                data.get("condition", ""), data.get("purchase_date", ""), data.get("purchase_cost", ""),
                data.get("warranty", "No"), data.get("supplier", ""), data.get("journal", ""),
                data.get("owner", ""), "", "", "", "", "", "Active", tahun
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
        ref_data = get_cached_data("sync_references", _load_sync_references)
        assets_ws = get_worksheet("Assets")
        if not assets_ws: return
        
        headers = assets_ws.row_values(1)
        data = assets_ws.get_all_values()[1:]
        
        if not data:
            logging.info("No asset data to sync")
            return
            
        updated_data = []
        tracker = defaultdict(int)
        tahun_berjalan = datetime.now().year
        
        # Pre-calculate header indices for performance
        header_indices = {header: i for i, header in enumerate(headers)}

        # Process rows with optimized field updates
        for i, row in enumerate(data):
            row_dict = dict(zip(headers, row))
            updated = list(row)  # Create copy
            
            # Update ID
            if "ID" in header_indices:
                updated[header_indices["ID"]] = str(i + 1)

            try:
                tahun_pembelian = datetime.strptime(row_dict.get("Purchase Date", ""), "%Y-%m-%d").year
            except:
                tahun_pembelian = tahun_berjalan

            # Calculate depreciation values
            cat_data = ref_data["categories"].get(row_dict.get("Category", ""), ["", "0", "1"])
            if len(cat_data) >= 3:
                code_category, residual_percent_raw, useful_life_raw = cat_data[0], cat_data[1], cat_data[2]
            else:
                code_category, residual_percent_raw, useful_life_raw = "", "0", "1"
                
            residual_percent = to_decimal(residual_percent_raw)
            useful_life = to_int(useful_life_raw)

            purchase_cost = to_decimal(row_dict.get("Purchase Cost", "0"))
            residual_value = (purchase_cost * residual_percent / 100).quantize(Decimal("0.01"))
            depreciation_value = ((purchase_cost - residual_value) / useful_life).quantize(Decimal("0.01")) if useful_life > 0 else Decimal(0)
            
            umur = max(0, tahun_berjalan - tahun_pembelian)
            book_value = (purchase_cost - (depreciation_value * umur)).quantize(Decimal("0.01"))

            # Generate asset tag
            code_company = ref_data["companies"].get(row_dict.get("Company", ""), "")
            code_owner = ref_data["owners"].get(row_dict.get("Owner", ""), "")
            code_type = ref_data["types"].get((row_dict.get("Type", ""), row_dict.get("Category", "")), "")

            key = (code_company, code_type, str(tahun_pembelian))
            tracker[key] += 1
            no_urut = str(tracker[key]).zfill(3)
            tahun_2digit = str(tahun_pembelian)[-2:]
            asset_tag = f"{code_company}-{code_category}{code_type}.{code_owner}{tahun_2digit}.{no_urut}"

            # Update row with calculated values using pre-calculated indices
            field_updates = {
                "Tahun": str(tahun_pembelian), "Code Category": code_category,
                "Residual Percent": str(residual_percent), "Useful Life": str(useful_life),
                "Residual Value": str(residual_value), "Depreciation Value": str(depreciation_value),
                "Book Value": str(book_value), "Code Company": code_company,
                "Code Owner": code_owner, "Code Type": code_type, "Asset Tag": asset_tag
            }

            for field, value in field_updates.items():
                if field in header_indices:
                    updated[header_indices[field]] = value

            updated_data.append(updated)

        # Batch update all data at once
        if updated_data:
            assets_ws.update([headers] + updated_data)
            logging.info(f"Successfully synced {len(updated_data)} assets")

    except Exception as e:
        logging.error(f"Gagal sinkronisasi data aset: {e}")
        raise

@retry_on_api_error()
def _load_sync_references() -> dict:
    """Load all reference data for sync operation"""
    ref_data = {"categories": {}, "types": {}, "companies": {}, "owners": {}}
    
    try:
        worksheets = {
            "categories": get_worksheet("Ref_Categories"),
            "types": get_worksheet("Ref_Types"),
            "companies": get_worksheet("Ref_Companies"),
            "owners": get_worksheet("Ref_Owners")
        }
        
        # Load categories with codes and depreciation info
        if worksheets["categories"]:
            for row in worksheets["categories"].get_all_values()[1:]:
                if len(row) >= 3:
                    ref_data["categories"][row[0]] = row[1:]
        
        # Load types
        if worksheets["types"]:
            for row in worksheets["types"].get_all_values()[1:]:
                if len(row) >= 3:
                    ref_data["types"][(row[0], row[1])] = row[2]
        
        # Load companies
        if worksheets["companies"]:
            for row in worksheets["companies"].get_all_values()[1:]:
                if len(row) >= 2:
                    ref_data["companies"][row[0]] = row[1]
        
        # Load owners
        if worksheets["owners"]:
            for row in worksheets["owners"].get_all_values()[1:]:
                if len(row) >= 2:
                    ref_data["owners"][row[0]] = row[1]
        
        return ref_data
    except Exception as e:
        logging.warning(f"Gagal load sync references: {e}")
        return ref_data
