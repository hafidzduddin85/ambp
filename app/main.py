import io
from collections import Counter
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openpyxl import Workbook

from app.sheets import (
    append_asset,
    get_assets,
    get_reference_lists,
    add_type_if_not_exists,
    add_category_if_not_exists,
    add_company_with_code_if_not_exists,
    add_owner_if_not_exists,
)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Static & Favicon
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
async def show_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")

# ======= INPUT FORM =======
@app.get("/input", response_class=HTMLResponse)
async def show_form(request: Request):
    refs = get_reference_lists()
    return templates.TemplateResponse("input_form.html", {
        "request": request,
        "categories": refs["categories"],
        "types": refs["types"],
        "companies": refs["companies"],
        "owners": refs["owners"]
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
    code_company: str = Form(...),
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
    # Normalisasi input
    company = company.strip().upper()
    code_company = code_company.strip().upper()

    # Validasi code_company: harus 3 huruf kapital
    if not code_company.isalpha() or len(code_company) != 3:
        return HTMLResponse(
            "<h3>❌ Code Company harus terdiri dari 3 huruf kapital (contoh: ABC)</h3>", status_code=400
        )

    # Tambah referensi jika belum ada
    try:
        add_category_if_not_exists(category)
        add_type_if_not_exists(type_, category)
        add_company_with_code_if_not_exists(company, code_company)
        add_owner_if_not_exists(owner)
    except ValueError as e:
        return HTMLResponse(f"<h3>❌ {e}</h3>", status_code=400)

    # Tambahkan data aset ke sheet
    append_asset({
        "item_name": item_name,
        "category": category,
        "type": type_,
        "manufacture": manufacture,
        "model": model,
        "serial_number": serial_number,
        "company": company,
        "code_company": code_company,
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

# ======= DASHBOARD =======
@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request, status: str = Query(default="All")):
    data = get_assets(status) or []

    kategori_counter = Counter([row.get("Category", "") for row in data if row.get("Category")])
    tahun_counter = Counter([str(row.get("Tahun", "")) for row in data if row.get("Tahun")])

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "assets": data,
        "selected_status": status,
        "kategori_labels": list(kategori_counter),
        "kategori_values": list(kategori_counter.values()),
        "tahun_labels": sorted(tahun_counter),
        "tahun_values": [tahun_counter[t] for t in sorted(tahun_counter)],
    })

# ======= EXPORT EXCEL =======
@app.get("/export")
async def export_excel(status: str = Query(default="All")):
    data = get_assets(status) or []

    wb = Workbook()
    ws = wb.active
    ws.title = "Assets"

    if data:
        ws.append(list(data[0].keys()))
        for row in data:
            ws.append(list(row.values()))

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=assets_{status.lower()}.xlsx"}
    )
