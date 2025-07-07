from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.sheets import append_asset

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/input", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("input_form.html", {"request": request})

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

