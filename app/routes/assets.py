# app/routes/assets.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils import sheets
from app.database.dependencies import get_current_user
from app.utils.flash import flash, get_flashed_messages

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/assets")
def list_assets(request: Request, status: str = "All", search: str = "", user=Depends(get_current_user)):
    try:
        assets = sheets.get_assets(status)
        
        # Search filter
        if search:
            assets = [
                asset for asset in assets 
                if search.lower() in str(asset.get('Item Name', '')).lower() or
                   search.lower() in str(asset.get('Asset Tag', '')).lower() or
                   search.lower() in str(asset.get('ID', '')).lower() or
                   search.lower() in str(asset.get('Category', '')).lower()
            ]
        
        flash_messages = get_flashed_messages(request)
        
        return templates.TemplateResponse("assets_list.html", {
            "request": request,
            "assets": assets,
            "selected_status": status,
            "search_query": search,
            "flash_messages": flash_messages,
            "user": user
        })
        
    except Exception as e:
        flash(request, f"❌ Error loading assets: {str(e)}", "error")
        return RedirectResponse(url="/home", status_code=303)

@router.get("/assets/{asset_id}/detail")
def asset_detail(request: Request, asset_id: str, user=Depends(get_current_user)):
    try:
        assets = sheets.get_assets("All")
        asset = next((a for a in assets if str(a.get('ID', '')) == asset_id), None)
        
        if not asset:
            flash(request, f"❌ Asset with ID {asset_id} not found", "error")
            return RedirectResponse(url="/assets", status_code=303)
        
        flash_messages = get_flashed_messages(request)
        
        return templates.TemplateResponse("asset_detail.html", {
            "request": request,
            "asset": asset,
            "flash_messages": flash_messages
        })
        
    except Exception as e:
        flash(request, f"❌ Error loading asset detail: {str(e)}", "error")
        return RedirectResponse(url="/assets", status_code=303)

@router.post("/assets/{asset_id}/status")
def change_status(
    request: Request, 
    asset_id: str, 
    new_status: str = Form(...),
    user=Depends(get_current_user)
):
    try:
        assets_ws = sheets.get_worksheet("Assets")
        if not assets_ws:
            flash(request, "❌ Cannot access assets data", "error")
            return RedirectResponse(url="/assets", status_code=303)
        
        headers = assets_ws.row_values(1)
        data = assets_ws.get_all_values()
        
        status_col = headers.index("Status") if "Status" in headers else None
        id_col = headers.index("ID") if "ID" in headers else 0
        
        if status_col is None:
            flash(request, "❌ Cannot find status column", "error")
            return RedirectResponse(url="/assets", status_code=303)
        
        # Find asset row
        for i, row in enumerate(data[1:], start=2):
            if len(row) > id_col and row[id_col] == asset_id:
                assets_ws.update_cell(i, status_col + 1, new_status)
                flash(request, f"✅ Asset {asset_id} status changed to {new_status}", "success")
                return RedirectResponse(url="/assets", status_code=303)
        
        flash(request, f"❌ Asset {asset_id} not found", "error")
        
    except Exception as e:
        flash(request, f"❌ Error changing status: {str(e)}", "error")
    
    return RedirectResponse(url="/assets", status_code=303)

@router.get("/assets/{asset_id}/delete")
def delete_asset(request: Request, asset_id: str, user=Depends(get_current_user)):
    try:
        # Check if user is admin
        if not user or user.get("role") != "admin":
            flash(request, "❌ Admin privileges required", "error")
            return RedirectResponse(url="/assets", status_code=303)
        
        assets_ws = sheets.get_worksheet("Assets")
        if not assets_ws:
            flash(request, "❌ Cannot access assets data", "error")
            return RedirectResponse(url="/assets", status_code=303)
        
        headers = assets_ws.row_values(1)
        data = assets_ws.get_all_values()
        id_col = headers.index("ID") if "ID" in headers else 0
        
        # Find and delete asset row
        for i, row in enumerate(data[1:], start=2):
            if len(row) > id_col and row[id_col] == asset_id:
                assets_ws.delete_rows(i)
                flash(request, f"✅ Asset {asset_id} deleted successfully", "success")
                return RedirectResponse(url="/assets", status_code=303)
        
        flash(request, f"❌ Asset {asset_id} not found", "error")
        
    except Exception as e:
        flash(request, f"❌ Error deleting asset: {str(e)}", "error")
    
    return RedirectResponse(url="/assets", status_code=303)