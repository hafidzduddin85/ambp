from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Query
from collections import Counter

from app.sheets import append_asset, get_sheet

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


@app.get("/input", response_class=HTMLResponse)
async def show_form(request: Request):
    sheet = get_sheet()

    # Ambil data referensi dari Google Sheets
    ref_categories = sheet.worksheet("Ref_Categories").col_values(1)[1:]  # Category
    ref_types = sheet.worksheet("Ref_Types").col_values(1)[1:]           # Type
    ref_companies = sheet.worksheet("Ref_Companies").col_values(1)[1:]   # Company
    ref_owners = sheet.worksheet("Ref_Owners").col_values(1)[1:]         # Owner

    return templates.TemplateResponse("input_form.html", {
        "request": request,
        "categories": ref_categories,
        "types": ref_types,
        "companies": ref_companies,
        "owners": ref_owners
    })


@app.post("/input")
async def submit_form(
    request: Request,
    item_name: str = Form(...),
    category: str = Form(...),
    type_: str = Form(...),
    manufacture: str = Form(""),
    model: str = Form(""),
    serial_number: str = Form(""),
    company: str = Form(...),
    bisnis_unit: str = Form(""),
    location: str = Form(""),
    room_location: str = Form(""),
    notes: str = Form(""),
    condition: str = Form(""),
    purchase_date: str = Form(...),
    purchase_cost: str = Form(...),
    warranty: str = Form("No"),
    supplier: str = Form(""),
    journal: str = Form(""),
    owner: str = Form(...)
):
    append_asset({
        "item_name": item_name,
        "category": category,
        "type": type_,
        "manufacture": manufacture,
        "model": model,
        "serial_number": serial_number,
        "company": company,
        "bisnis_unit": bisnis_unit,
        "location": location,
        "room_location": room_location,
        "notes": notes,
        "condition": condition,
        "purchase_date": purchase_date,
        "purchase_cost": purchase_cost,
        "warranty": warranty,
        "supplier": supplier,
        "journal": journal,
        "owner": owner,
    })
    return RedirectResponse(url="/input", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request, status: str = Query(default="All")):
    sheet = get_sheet()
    data = sheet.worksheet("Assets").get_all_records()

    # Filter berdasarkan status
    filtered = data
    if status != "All":
        filtered = [row for row in data if row.get("Status", "").lower() == status.lower()]

    # Hitung grafik berdasarkan data terfilter
    kategori_counter = Counter([row["Category"] for row in filtered if row.get("Category")])
    tahun_counter = Counter([str(row.get("Tahun", "")) for row in filtered if row.get("Tahun")])

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "assets": filtered,
        "selected_status": status,
        "kategori_labels": list(kategori_counter.keys()),
        "kategori_values": list(kategori_counter.values()),
        "tahun_labels": list(tahun_counter.keys()),
        "tahun_values": list(tahun_counter.values()),
    })

