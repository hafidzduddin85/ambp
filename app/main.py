from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import sheets
import uvicorn

app = FastAPI()

# Static & Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/input", response_class=HTMLResponse)
def show_form(request: Request):
    refs = sheets.get_reference_lists()
    location_room_map = sheets.get_location_room_map()
    return templates.TemplateResponse("input_form.html", {
        "request": request,
        "refs": refs,
        "location_room_map": location_room_map
    })

@app.post("/submit")
def submit_asset(
    request: Request,
    item_name: str = Form(...),
    category: str = Form(...),
    type: str = Form(...),
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
    purchase_date: str = Form(""),
    purchase_cost: str = Form(""),
    warranty: str = Form("No"),
    supplier: str = Form(""),
    journal: str = Form(""),
    owner: str = Form(...),
    new_company: str = Form(""),
    new_code_company: str = Form(""),
    new_location: str = Form(""),
    new_room_location: str = Form(""),
):
    # Tambah company baru jika diisi
    if new_company and new_code_company:
        sheets.add_company_with_code_if_not_exists(new_company, new_code_company)
        company = new_company
        code_company = new_code_company

    # Tambah location-room jika diisi
    if new_location and new_room_location:
        sheets.add_location_if_not_exists(new_location, new_room_location)
        location = new_location
        room_location = new_room_location

    # Tambah kategori/tipe/owner jika baru
    sheets.add_category_if_not_exists(category)
    sheets.add_type_if_not_exists(type, category)
    sheets.add_owner_if_not_exists(owner)

    data = {
        "item_name": item_name,
        "category": category,
        "type": type,
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

    sheets.append_asset(data)
    return RedirectResponse(url="/input", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, status: str = "All"):
    data = sheets.get_assets(status)

    kategori_summary = {}
    tahun_summary = {}
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

@app.get("/export")
def export_excel(status: str = "All"):
    data = sheets.get_assets(status)
    from fastapi.responses import StreamingResponse
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=assets_{status}.csv"}
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
