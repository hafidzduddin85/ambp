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


def get_next_asset_id() -> str:
    sheet = get_sheet()
    ws = sheet.worksheet("Assets")
    ids = ws.col_values(1)  # kolom A = ID

    # Ambil ID terakhir yang valid
    angka_terakhir = 0
    for id_val in ids[1:]:  # skip header
        if id_val.startswith("A") and id_val[1:].isdigit():
            angka = int(id_val[1:])
            angka_terakhir = max(angka_terakhir, angka)

    # Tambahkan 1 dan format jadi A001, A002, ...
    next_id = angka_terakhir + 1
    return f"A{str(next_id).zfill(3)}"
