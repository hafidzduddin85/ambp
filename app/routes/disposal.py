# app/routes/disposal.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils import sheets
from app.database.dependencies import get_current_user
from app.utils.flash import flash, get_flashed_messages
from datetime import datetime, timezone

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/disposal")
def disposal_page(request: Request, user=Depends(get_current_user)):
    try:
        # Get assets that can be disposed (To be Disposed status)
        assets = sheets.get_assets("To be Disposed")
        flash_messages = get_flashed_messages(request)
        
        return templates.TemplateResponse("disposal.html", {
            "request": request,
            "assets": assets,
            "flash_messages": flash_messages,
            "user": user
        })
        
    except Exception as e:
        flash(request, f"❌ Error loading disposal page: {str(e)}", "error")
        return RedirectResponse(url="/home", status_code=303)

@router.post("/disposal/{asset_id}/dispose")
def dispose_asset(
    request: Request,
    asset_id: str,
    disposal_method: str = Form(...),
    disposal_value: str = Form("0"),
    notes: str = Form(""),
    user=Depends(get_current_user)
):
    try:
        # Check admin privileges
        if not user or user.get("role") != "admin":
            flash(request, "❌ Admin privileges required", "error")
            return RedirectResponse(url="/disposal", status_code=303)
        
        assets_ws = sheets.get_worksheet("Assets")
        if not assets_ws:
            flash(request, "❌ Cannot access assets data", "error")
            return RedirectResponse(url="/disposal", status_code=303)
        
        headers = assets_ws.row_values(1)
        data = assets_ws.get_all_values()
        
        status_col = headers.index("Status") if "Status" in headers else None
        id_col = headers.index("ID") if "ID" in headers else 0
        item_name_col = headers.index("Item Name") if "Item Name" in headers else None
        
        if status_col is None:
            flash(request, "❌ Cannot find status column", "error")
            return RedirectResponse(url="/disposal", status_code=303)
        
        # Find asset and update status to Disposed
        for i, row in enumerate(data[1:], start=2):
            if len(row) > id_col and row[id_col] == asset_id:
                asset_name = row[item_name_col] if item_name_col and len(row) > item_name_col else ""
                
                # Update status to Disposed
                assets_ws.update_cell(i, status_col + 1, "Disposed")
                
                # Log disposal
                log_disposal(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    disposal_method=disposal_method,
                    disposal_value=disposal_value,
                    disposed_by=user.get("username", "Unknown"),
                    notes=notes
                )
                
                flash(request, f"✅ Asset {asset_id} successfully disposed", "success")
                return RedirectResponse(url="/disposal", status_code=303)
        
        flash(request, f"❌ Asset {asset_id} not found", "error")
        
    except Exception as e:
        flash(request, f"❌ Error disposing asset: {str(e)}", "error")
    
    return RedirectResponse(url="/disposal", status_code=303)

def log_disposal(asset_id: str, asset_name: str, disposal_method: str, 
                disposal_value: str, disposed_by: str, notes: str = ""):
    """Log disposal to Google Sheets"""
    try:
        log_ws = sheets.get_worksheet("Log_Disposal")
        if not log_ws:
            # Create sheet if doesn't exist
            sheet = sheets.get_sheet()
            log_ws = sheet.add_worksheet(title="Log_Disposal", rows=1000, cols=8)
            # Add headers
            headers = [
                "Timestamp", "Asset ID", "Asset Name", "Disposal Method", 
                "Disposal Value", "Disposed By", "Notes", "Status"
            ]
            log_ws.append_row(headers)
        
        # Add log entry
        log_entry = [
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            asset_id,
            asset_name,
            disposal_method,
            disposal_value,
            disposed_by,
            notes,
            "Disposed"
        ]
        
        log_ws.append_row(log_entry)
        
    except Exception as e:
        print(f"Error logging disposal: {e}")

@router.get("/disposal/logs")
def disposal_logs(request: Request, user=Depends(get_current_user)):
    """View disposal logs"""
    try:
        log_ws = sheets.get_worksheet("Log_Disposal")
        if not log_ws:
            logs = []
        else:
            logs = log_ws.get_all_records()
            # Sort by timestamp descending (newest first)
            logs = sorted(logs, key=lambda x: x.get("Timestamp", ""), reverse=True)
        
        flash_messages = get_flashed_messages(request)
        
        return templates.TemplateResponse("disposal_logs.html", {
            "request": request,
            "logs": logs,
            "flash_messages": flash_messages,
            "user": user
        })
        
    except Exception as e:
        flash(request, f"❌ Error loading disposal logs: {str(e)}", "error")
        return RedirectResponse(url="/disposal", status_code=303)