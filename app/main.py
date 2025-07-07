from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from datetime import datetime
from typing import Optional
import uvicorn

from app.sheet import (
    get_reference_lists,
    append_asset,
    add_category_if_not_exists,
    add_type_if_not_exists,
    add_company_with_code_if_not_exists,
    add_owner_if_not_exists,
    get_assets,
    get_location_room_map,
    add_location_if_not_exists
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/input", response_class=HTMLResponse)
async def show_form(request: Request):
    refs = get_reference_lists()
    room_map = get_location_room_map()
    return templates.TemplateResponse("input_form.html", {
        "request": request,
        **refs,
        "room_map": room_map,
        "locations": list(room_map.keys())
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
    location: str = Form(...),
    room_location: str = Form(...),
    notes: str = Form(""),
    condition: str = Form(""),
    purchase_date: str = Form(...),
    purchase_cost: float = Form(...),
    warranty: str = Form("No"),
    supplier: str = Form(""),
    journal: str = Form(""),
    owner: str = Form(...)
):
    # Pastikan referensi ditambahkan jika belum ada
    add_category_if_not_exists(category)
    add_type_if_not_exists(type_, category)
    add_company_with_code_if_not_exists(company, code_company)
    add_owner_if_not_exists(owner)
    add_location_if_not_exists(location, room_location)

    data = {
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
        "owner": owner
    }

    append_asset(data)
    return RedirectResponse("/input", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, status: Optional[str] = "All"):
    assets = get_assets(status)
    kategori_count = {}
    tahun_count = {}
    for a in assets:
        kategori = a.get("Category", "-")
        kategori_count[kategori] = kategori_count.get(kategori, 0) + 1

        tahun = a.get("Tahun", datetime.now().year)
        tahun_count[tahun] = tahun_count.get(tahun, 0) + 1

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "assets": assets,
        "selected_status": status,
        "kategori_labels": list(kategori_count.keys()),
        "kategori_values": list(kategori_count.values()),
        "tahun_labels": list(tahun_count.keys()),
        "tahun_values": list(tahun_count.values()),
    })

@app.get("/export")
async def export_excel(status: Optional[str] = "All"):
    assets = get_assets(status)

    from fastapi.responses import StreamingResponse
    import io
    import csv

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=assets[0].keys())
    writer.writeheader()
    for row in assets:
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=assets_{status}.csv"}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
