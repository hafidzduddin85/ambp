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
    company: str = Form(...),
    owner: str = Form(...),
    purchase_date: str = Form(...),
    purchase_cost: str = Form(...)
):
    append_asset({
        "item_name": item_name,
        "category": category,
        "type": type_,
        "company": company,
        "owner": owner,
        "purchase_date": purchase_date,
        "purchase_cost": purchase_cost,
    })
    return RedirectResponse(url="/input", status_code=303)
