# app/utils/fill_functions.py
from datetime import datetime
from decimal import Decimal

def get_id(index: int) -> str:
    return str(index)

def get_year(purchase_date: str) -> int:
    try:
        return datetime.strptime(purchase_date, "%Y-%m-%d").year if purchase_date else datetime.now().year
    except:
        return datetime.now().year

def get_residual_percent(ref_categories: dict, category: str) -> float:
    cat_data = ref_categories.get(category, {})
    return float(cat_data.get("Residual Percent", 0))

def get_useful_life(ref_categories: dict, category: str) -> int:
    cat_data = ref_categories.get(category, {})
    return int(cat_data.get("Useful Life", 1))

def get_residual_value(purchase_cost: float, residual_percent: float) -> float:
    return round(purchase_cost * residual_percent / 100, 2)

def get_depreciation(purchase_cost: float, residual_value: float, useful_life: int) -> float:
    if useful_life <= 0:
        return 0
    return round((purchase_cost - residual_value) / useful_life, 2)

def get_book_value(purchase_cost: float, depreciation_value: float, asset_year: int, current_year: int) -> float:
    age = max(0, current_year - asset_year)
    return round(purchase_cost - (depreciation_value * age), 2)

def get_code_category(ref_categories: dict, category: str) -> str:
    cat_data = ref_categories.get(category, {})
    return cat_data.get("Code Category", "")

def get_code_company(ref_companies: dict, company: str) -> str:
    comp_data = ref_companies.get(company, {})
    return comp_data.get("Code Company", "")

def get_code_type(ref_types: dict, type_name: str, category: str) -> str:
    type_key = f"{type_name}|{category}"
    type_data = ref_types.get(type_key, {})
    return type_data.get("Code Type", "")

def get_code_owner(ref_owners: dict, owner: str) -> str:
    owner_data = ref_owners.get(owner, {})
    return owner_data.get("Code Owner", "")

def generate_asset_tag(code_company: str, code_category: str, code_type: str, code_owner: str, year: int, tag_counters: dict) -> str:
    if not all([code_company, code_category, code_type, code_owner]):
        return ""
    
    key = (code_company, code_type, str(year))
    tag_counters[key] = tag_counters.get(key, 0) + 1
    seq_num = str(tag_counters[key]).zfill(3)
    year_2digit = str(year)[-2:]
    
    return f"{code_company}-{code_category}{code_type}.{code_owner}{year_2digit}.{seq_num}"