# app/routes/asset.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from io import StringIO
import csv
from app import sheets
from app.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/input", response_class=RedirectResponse)
def show_form(request: Request, user=Depends(get_current_user)):
    refs = sheets.get_reference_lists()
    location_room_map = sheets.get_location_room_map()
    return templates.TemplateResponse("input_form.html", {
        "request": request,
        "refs": refs,
        "location_room_map": location_room_map
    })

@router.post("/submit")
def submit_asset(
    request: Request,
    item_name: str = Form(...),
    category: str = Form(...),
    code_category: str = Form(...),
    type: str = Form(...),
    manufacture: str = Form(""),
    model: str = Form(""),
    serial_number: str = Form(""),
    company: str = Form(...),
    code_company: str = Form(""),
    bisnis_unit: str = Form(""),
    location: str = Form(...),
    room_location: str = Form(...),
    notes: str = Form(""),
    condition: str = Form(""),
    purchase_date: str = Form(""),
    purchase_cost: str = Form(""),
    warranty: str = Form("No"),
    supplier: str = Form(""),
    journal: str = Form(""),
    owner: str = Form(...),
    code_owner: str = Form(...),
    user=Depends(get_current_user)
):
    sheets.add_type_if_not_exists(type, category)
    sheets.add_location_if_not_exists(location, room_location)
    sheets.add_company_with_code_if_not_exists(company, code_company)
    sheets.add_owner_if_not_exists(owner, code_owner)
    sheets.add_category_if_not_exists(category, code_category)

    data = {
        "item_name": item_name, "category": category, "code_category": code_category, "type": type,
        "manufacture": manufacture, "model": model, "serial_number": serial_number,
        "company": company, "code_company": code_company, "bisnis_unit": bisnis_unit,
        "location": location, "room_location": room_location, "notes": notes,
        "condition": condition, "purchase_date": purchase_date, "purchase_cost": purchase_cost,
        "warranty": warranty, "supplier": supplier, "journal": journal, "owner": owner, "code_owner": code_owner
    }

    sheets.append_asset(data)
    return RedirectResponse(url="/input", status_code=303)

@router.get("/dashboard", response_class=RedirectResponse)
def dashboard(request: Request, status: str = "All", user=Depends(get_current_user)):
    data = sheets.get_assets(status)
    kategori_summary, tahun_summary = {}, {}

    for row in data:
        kategori = row.get("Category", "Lainnya")
        kategori_summary[kategori] = kategori_summary.get(kategori, 0) + 1
        tahun = str(row.get("Tahun", ""))
        if tahun:
            tahun_summary[tahun] = tahun_summary.get(tahun, 0) + 1

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "selected_status": status,
        "assets": data,
        "kategori_labels": list(kategori_summary.keys()),
        "kategori_values": list(kategori_summary.values()),
        "tahun_labels": list(tahun_summary.keys()),
        "tahun_values": list(tahun_summary.values()),
    })

@router.get("/export")
def export_excel(status: str = "All", user=Depends(get_current_user)):
    data = sheets.get_assets(status)
    if not data:
        output = StringIO()
        output.write("No data available")
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=assets_{status}.csv"})
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=assets_{status}.csv"})
