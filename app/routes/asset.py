# app/routes/asset.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from io import StringIO
import csv
from app.utils import sheets
from app.database.dependencies import get_current_user
from app.utils.references import validate_category_or_default
from app.utils.flash import flash

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/input")
def show_form(request: Request, user=Depends(get_current_user)):
    from app.utils.flash import get_flashed_messages
    from fastapi import HTTPException, status
    
    # Check if user is admin
    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    
    refs = sheets.get_reference_lists()
    location_room_map = sheets.get_location_room_map()
    flash_messages = get_flashed_messages(request)
    
    return templates.TemplateResponse("input_form.html", {
        "request": request,
        "refs": refs,
        "location_room_map": location_room_map,
        "flash_messages": flash_messages
    })

@router.post("/submit")
def submit_asset(
    request: Request,
    item_name: str = Form(...),
    category: str = Form(...),
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
    user=Depends(get_current_user)
):
    from fastapi import HTTPException, status
    
    # Check if user is admin
    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    from app.utils.references import add_type_if_not_exists, add_location_if_not_exists, add_company_with_code_if_not_exists, add_owner_if_not_exists, add_category_if_not_exists
    
    category = validate_category_or_default(category)
    
    # Extract company name if in "Company (CODE)" format
    company_name = company.split(" (")[0] if " (" in company else company

    # Add references if they don't exist
    add_type_if_not_exists(type, category)
    add_location_if_not_exists(location, room_location)
    add_company_with_code_if_not_exists(company_name, code_company)
    add_owner_if_not_exists(owner, "")
    add_category_if_not_exists(category, "")

    data = {
        "item_name": item_name, "category": category, "type": type,
        "manufacture": manufacture, "model": model, "serial_number": serial_number,
        "company": company_name, "bisnis_unit": bisnis_unit,
        "location": location, "room_location": room_location, "notes": notes,
        "condition": condition, "purchase_date": purchase_date, "purchase_cost": purchase_cost,
        "warranty": warranty, "supplier": supplier, "journal": journal, "owner": owner
    }

    try:
        sheets.append_asset(data)
        flash(request, f"✅ Aset '{item_name}' berhasil ditambahkan!", "success")
    except Exception as e:
        flash(request, f"❌ Gagal menambahkan aset: {str(e)}", "error")
    
    return RedirectResponse(url="/input", status_code=303)

@router.get("/dashboard")
def dashboard(request: Request, status: str = "All", user=Depends(get_current_user)):
    data = sheets.get_assets(status)
    all_data = sheets.get_assets("All")  # For statistics
    
    kategori_summary, tahun_summary = {}, {}
    active_count = repair_count = disposed_count = 0

    # Process filtered data for charts
    for row in data:
        kategori = row.get("Category", "Others")
        kategori_summary[kategori] = kategori_summary.get(kategori, 0) + 1
        tahun = str(row.get("Tahun", ""))
        if tahun and tahun != "":
            tahun_summary[tahun] = tahun_summary.get(tahun, 0) + 1
    
    # Process all data for statistics
    for row in all_data:
        asset_status = row.get("Status", "").lower()
        if asset_status in ["active"]:
            active_count += 1
        elif asset_status in ["under repair"]:
            repair_count += 1
        elif asset_status in ["disposed", "to be disposed"]:
            disposed_count += 1

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "selected_status": status,
        "assets": data,
        "kategori_labels": list(kategori_summary.keys()),
        "kategori_values": list(kategori_summary.values()),
        "tahun_labels": sorted(list(tahun_summary.keys())),
        "tahun_values": [tahun_summary[year] for year in sorted(tahun_summary.keys())],
        "active_count": active_count,
        "repair_count": repair_count,
        "disposed_count": disposed_count,
        "user": user,
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

@router.post("/sync")
def sync_data(request: Request, user=Depends(get_current_user)):
    """Sync asset data - fill empty columns with calculated values"""
    try:
        from app.utils.sheets import sync_assets_data
        result = sync_assets_data()
        flash(request, f"🔄 {result.get('message', 'Sync completed')}", "success")
        return {"success": True, "message": f"Synced: {result.get('message', '')}", "data": result}
    except Exception as e:
        flash(request, f"❌ Sync failed: {str(e)}", "error")
        return {"success": False, "message": f"Sync failed: {str(e)}"}
