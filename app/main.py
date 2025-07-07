import io
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from collections import Counter
from openpyxl import Workbook

from app.sheets import append_asset, get_sheet

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Serve static files (for manifest, icons, service worker, etc.)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/dashboard")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")


@app.get("/input", response_class=HTMLResponse)
async def show_form(request: Request):
    sheet = get_sheet()

    ref_categories = sheet.worksheet("Ref_Categories").col_values(1)[1:]
    ref_types = sheet.worksheet("Ref_Types").col_values(1)[1:]
    ref_companies = sheet.worksheet("Ref_Companies").col_values(1)[1:]
    ref_owners = sheet.worksheet("Ref_Owners").col_values(1)[1:]

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

    if status != "All":
        filtered = [row for row in data if row.get("Status", "").lower() == status.lower()]
    else:
        filtered = data

    kategori_counter = Counter([row["Category"] for row in filtered if row.get("Category")])
    tahun_counter = Counter([str(row.get("Tahun", "")) for row in filtered if row.get("Tahun")])

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "assets": filtered,
        "selected_status": status,
        "kategori_labels": list(kategori_counter.keys()),
        "kategori_values": list(kategori_counter.values()),
        "tahun_labels": sorted(tahun_counter.keys()),
        "tahun_values": [tahun_counter[t] for t in sorted(tahun_counter.keys())],
    })


@app.get("/export")
async def export_excel(status: str = Query(default="All")):
    sheet = get_sheet()
    data = sheet.worksheet("Assets").get_all_records()

    if status != "All":
        data = [row for row in data if row.get("Status", "").lower() == status.lower()]

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
