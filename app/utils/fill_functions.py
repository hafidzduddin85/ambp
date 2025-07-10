# app/utils/fill_functions.py
from datetime import datetime

def get_id(index: int) -> int:
    return index  # baris ke-n

def get_year(purchase_date_str: str) -> int:
    try:
        return datetime.strptime(purchase_date_str, "%Y-%m-%d").year
    except Exception:
        return 0

def get_residual_percent(ref_categories: dict, category: str) -> float:
    return float(ref_categories.get(category, {}).get("Residual Percent", 0))

def get_useful_life(ref_categories: dict, category: str) -> float:
    return float(ref_categories.get(category, {}).get("Useful Life", 1))

def get_residual_value(cost: float, residual_percent: float) -> float:
    return round((residual_percent / 100) * cost, 2)

def get_depreciation(cost: float, residual_value: float, useful_life: float) -> float:
    try:
        return round((cost - residual_value) / useful_life, 2)
    except ZeroDivisionError:
        return 0

def get_book_value(cost: float, depreciation: float, purchase_year: int, current_year: int) -> float:
    return round(cost - (depreciation * (current_year - purchase_year)), 2)

def get_code_category(ref_categories: dict, category: str) -> str:
    return ref_categories.get(category, {}).get("Code Category", "XX")

def get_code_company(ref_companies: dict, company: str) -> str:
    return ref_companies.get(company, {}).get("Code Company", "XXX")

def get_code_type(ref_types: dict, type_: str, category: str) -> str:
    return ref_types.get(f"{type_}|{category}", {}).get("Code Type", "XX")

def get_code_owner(ref_owners: dict, owner: str) -> str:
    return ref_owners.get(owner, {}).get("Code Owner", "XX")

def generate_asset_tag(code_company, code_category, code_type, code_owner, year, tag_counters) -> str:
    short_year = str(year)[-2:]
    tag_key = f"{code_company}-{code_category}{code_type}.{code_owner}{short_year}"

    if tag_key not in tag_counters:
        tag_counters[tag_key] = 1
    no_urut = str(tag_counters[tag_key]).zfill(3)
    tag_counters[tag_key] += 1

    return f"{tag_key}.{no_urut}"
