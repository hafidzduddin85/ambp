# sheets.py (refactored)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Dict, List
from app.config import load_config
from app.utils.fill_functions import *
from app.utils.references import get_reference_data

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
config = load_config()
creds = ServiceAccountCredentials.from_json_keyfile_dict(config.GOOGLE_CREDS_JSON, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(config.GOOGLE_SHEET_ID)


def get_assets(status="All") -> List[Dict]:
    ws = sheet.worksheet("Assets")
    data = ws.get_all_records()
    return [row for row in data if status == "All" or row.get("Status") == status]


def get_reference_lists() -> Dict:
    categories = get_reference_data(sheet, "Ref_Categories", "Category")
    types = get_reference_data(sheet, "Ref_Types", "Type", composite_key=("Type", "Category"))
    companies = get_reference_data(sheet, "Ref_Companies", "Company")
    owners = get_reference_data(sheet, "Ref_Owners", "Owner")
    locations = get_reference_data(sheet, "Ref_Location", "Location")

    return {
        "categories": list(categories.keys()),
        "types": [dict(Type=k.split("|")[0], Category=k.split("|")[1]) for k in types.keys()],
        "companies": list(companies.keys()),
        "owners": list(owners.keys()),
        "locations": list(locations.keys()),
    }


def get_location_room_map() -> Dict[str, List[str]]:
    values = sheet.worksheet("Ref_Location").get_all_records()
    location_map = {}
    for row in values:
        loc = row.get("Location", "")
        room = row.get("Room", "")
        if loc:
            if loc not in location_map:
                location_map[loc] = []
            if room and room not in location_map[loc]:
                location_map[loc].append(room)
    return location_map


def append_asset(data: Dict):
    ws = sheet.worksheet("Assets")
    headers = ws.row_values(1)
    existing_data = ws.get_all_values()
    index = len(existing_data)

    # Ambil referensi
    ref_categories = get_reference_data(sheet, "Ref_Categories", "Category")
    ref_types = get_reference_data(sheet, "Ref_Types", "Type", composite_key=("Type", "Category"))
    ref_companies = get_reference_data(sheet, "Ref_Companies", "Company")
    ref_owners = get_reference_data(sheet, "Ref_Owners", "Owner")

    tag_counters = {}  # Untuk asset tag
    current_year = datetime.now().year

    # Hitung field otomatis
    asset = {key: data.get(key, "") for key in headers}  # Init dict dengan header
    purchase_cost = float(data.get("purchase_cost") or 0)
    purchase_date = data.get("purchase_date")
    year = get_year(purchase_date)

    asset["ID"] = get_id(index)
    asset["Tahun"] = year
    asset["Residual Percent"] = get_residual_percent(ref_categories, data["category"])
    asset["Useful Life"] = get_useful_life(ref_categories, data["category"])
    asset["Residual Value"] = get_residual_value(purchase_cost, asset["Residual Percent"])
    asset["Depreciation Value"] = get_depreciation(purchase_cost, asset["Residual Value"], asset["Useful Life"])
    asset["Book Value"] = get_book_value(purchase_cost, asset["Depreciation Value"], year, current_year)
    asset["Code Category"] = get_code_category(ref_categories, data["category"])
    asset["Code Company"] = get_code_company(ref_companies, data["company"])
    asset["Code Type"] = get_code_type(ref_types, data["type"], data["category"])
    asset["Code Owner"] = get_code_owner(ref_owners, data["owner"])
    asset["Asset Tag"] = generate_asset_tag(
        asset["Code Company"], asset["Code Category"], asset["Code Type"],
        asset["Code Owner"], year, tag_counters
    )

    # Urutkan sesuai header
    values = [asset.get(h, "") for h in headers]
    ws.append_row(values)
