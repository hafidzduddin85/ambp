# app/routes/assets.py
from fastapi import APIRouter, Request, Form, Depends, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils import sheets
from app.database.dependencies import get_current_user
from app.utils.flash import flash, get_flashed_messages
from app.utils.photo import resize_and_convert_image, upload_to_drive, delete_from_drive
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/assets")
def list_assets(request: Request, status: str = "All", search: str = "", user=Depends(get_current_user)):
    try:
        assets = sheets.get_assets(status)
        
        # Enhanced search filter - focus on key fields
        if search:
            search_term = search.lower().strip()
            filtered_assets = []
            
            for asset in assets:
                # Primary search fields (most important)
                primary_fields = [
                    str(asset.get('Item Name', '')),
                    str(asset.get('Category', '')),
                    str(asset.get('Type', '')),
                    str(asset.get('Location', ''))
                ]
                
                # Secondary search fields
                secondary_fields = [
                    str(asset.get('Asset Tag', '')),
                    str(asset.get('ID', '')),
                    str(asset.get('Manufacture', '')),
                    str(asset.get('Model', '')),
                    str(asset.get('Company', '')),
                    str(asset.get('Room Location', ''))
                ]
                
                # Check primary fields first (higher priority)
                primary_match = any(search_term in field.lower() for field in primary_fields)
                secondary_match = any(search_term in field.lower() for field in secondary_fields)
                
                if primary_match or secondary_match:
                    filtered_assets.append(asset)
            
            assets = filtered_assets
        
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
            "flash_messages": flash_messages,
            "user": user
        })
        
    except Exception as e:
        flash(request, f"❌ Error loading asset detail: {str(e)}", "error")
        return RedirectResponse(url="/assets", status_code=303)

@router.post("/assets/{asset_id}/photo")
def upload_photo(
    request: Request,
    asset_id: str,
    photo: UploadFile = File(...),
    user=Depends(get_current_user)
):
    try:
        # Validate file type
        if not photo.content_type.startswith('image/'):
            flash(request, "❌ Please upload an image file", "error")
            return RedirectResponse(url=f"/assets/{asset_id}/detail", status_code=303)
        
        # Resize and convert to WebP
        resized_image = resize_and_convert_image(photo.file)
        if not resized_image:
            flash(request, "❌ Error processing image", "error")
            return RedirectResponse(url=f"/assets/{asset_id}/detail", status_code=303)
        
        # Upload to Google Drive
        image_url = upload_to_drive(resized_image, photo.filename, asset_id)
        if not image_url:
            flash(request, "❌ Error uploading image", "error")
            return RedirectResponse(url=f"/assets/{asset_id}/detail", status_code=303)
        
        # Update asset with photo URL
        assets_ws = sheets.get_worksheet("Assets")
        if assets_ws:
            headers = assets_ws.row_values(1)
            data = assets_ws.get_all_values()
            
            # Add Photo URL column if not exists
            if "Photo URL" not in headers:
                headers.append("Photo URL")
                assets_ws.update('1:1', [headers])
            
            photo_col = headers.index("Photo URL") + 1
            id_col = headers.index("ID") if "ID" in headers else 0
            
            # Find asset row and update photo URL
            for i, row in enumerate(data[1:], start=2):
                if len(row) > id_col and row[id_col] == asset_id:
                    assets_ws.update_cell(i, photo_col, image_url)
                    break
        
        flash(request, "✅ Photo uploaded successfully", "success")
        
    except Exception as e:
        flash(request, f"❌ Error uploading photo: {str(e)}", "error")
    
    return RedirectResponse(url=f"/assets/{asset_id}/detail", status_code=303)

@router.post("/assets/{asset_id}/status")
def change_status(
    request: Request, 
    asset_id: str, 
    new_status: str = Form(...),
    notes: str = Form(""),
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
        item_name_col = headers.index("Item Name") if "Item Name" in headers else None
        
        if status_col is None:
            flash(request, "❌ Cannot find status column", "error")
            return RedirectResponse(url="/assets", status_code=303)
        
        # Find asset row and get current data
        for i, row in enumerate(data[1:], start=2):
            if len(row) > id_col and row[id_col] == asset_id:
                old_status = row[status_col] if len(row) > status_col else ""
                asset_name = row[item_name_col] if item_name_col and len(row) > item_name_col else ""
                
                # Update status
                assets_ws.update_cell(i, status_col + 1, new_status)
                
                # Log status change
                log_status_change(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=user.get("username", "Unknown"),
                    notes=notes
                )
                
                flash(request, f"✅ Asset {asset_id} status changed to {new_status}", "success")
                return RedirectResponse(url="/assets", status_code=303)
        
        flash(request, f"❌ Asset {asset_id} not found", "error")
        
    except Exception as e:
        flash(request, f"❌ Error changing status: {str(e)}", "error")
    
    return RedirectResponse(url="/assets", status_code=303)

def log_status_change(asset_id: str, asset_name: str, old_status: str, new_status: str, 
                     changed_by: str, notes: str = ""):
    """Log status change to Google Sheets"""
    try:
        from datetime import datetime, timezone
        
        log_ws = sheets.get_worksheet("Log_Status")
        if not log_ws:
            # Create sheet if doesn't exist
            sheet = sheets.get_sheet()
            log_ws = sheet.add_worksheet(title="Log_Status", rows=1000, cols=8)
            # Add headers
            headers = [
                "Timestamp", "Asset ID", "Asset Name", "Old Status", 
                "New Status", "Changed By", "Notes", "Reason"
            ]
            log_ws.append_row(headers)
        
        # Add log entry
        log_entry = [
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            asset_id,
            asset_name,
            old_status,
            new_status,
            changed_by,
            notes,
            f"Status changed from {old_status} to {new_status}"
        ]
        
        log_ws.append_row(log_entry)
        
    except Exception as e:
        print(f"Error logging status change: {e}")

@router.get("/assets/logs/status")
def view_status_logs(request: Request, user=Depends(get_current_user)):
    """View status change logs"""
    try:
        log_ws = sheets.get_worksheet("Log_Status")
        if not log_ws:
            logs = []
        else:
            logs = log_ws.get_all_records()
            # Sort by timestamp descending (newest first)
            logs = sorted(logs, key=lambda x: x.get("Timestamp", ""), reverse=True)
        
        flash_messages = get_flashed_messages(request)
        
        return templates.TemplateResponse("status_logs.html", {
            "request": request,
            "logs": logs,
            "flash_messages": flash_messages
        })
        
    except Exception as e:
        flash(request, f"❌ Error loading status logs: {str(e)}", "error")
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