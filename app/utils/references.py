# app/utils/references.py
import gspread
from typing import Dict, Optional, Tuple

def get_reference_data(sheet: gspread.Spreadsheet, sheet_name: str, key_field: str, composite_key: Optional[Tuple[str, str]] = None) -> Dict:
    ws = sheet.worksheet(sheet_name)
    values = ws.get_all_records()
    ref_map = {}

    for row in values:
        if composite_key:
            key = f"{row[composite_key[0]]}|{row[composite_key[1]]}"
        else:
            key = row[key_field]
        ref_map[key] = row

    return ref_map

def add_type_if_not_exists(type_: str, category: str):
    ws = _get_sheet("Ref_Types")
    values = ws.get_all_records()

    for row in values:
        if row.get("Type") == type_ and row.get("Category") == category:
            return

    existing_for_category = [row for row in values if row.get("Category") == category]
    new_code = str(len(existing_for_category) + 1).zfill(2)
    ws.append_row([type_, category, new_code])

def validate_category_or_default(category: str) -> str:
    ws = _get_sheet("Ref_Categories")
    categories = {row["Category"] for row in ws.get_all_records()}
    return category if category in categories else "Others"

def add_location_if_not_exists(location: str, room: str):
    ws = _get_sheet("Ref_Location")
    values = ws.get_all_records()
    for row in values:
        if row.get("Location") == location and row.get("Room") == room:
            return
    ws.append_row([location, room])

def add_company_with_code_if_not_exists(company: str, code: str):
    ws = _get_sheet("Ref_Companies")
    values = ws.get_all_records()
    for row in values:
        if row.get("Company") == company:
            return
    ws.append_row([company, code])

def add_owner_if_not_exists(owner: str, code: str):
    ws = _get_sheet("Ref_Owners")
    values = ws.get_all_records()
    for row in values:
        if row.get("Owner") == owner:
            return
    ws.append_row([owner, code])

def add_category_if_not_exists(category: str, code: str):
    # Do nothing, category is fixed and should not be added dynamically
    return

def _get_sheet(sheet_name: str) -> gspread.Worksheet:
    from app.sheets import sheet  # avoid circular import
    return sheet.worksheet(sheet_name)
