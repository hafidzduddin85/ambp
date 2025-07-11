# app/routes/relocation.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils import sheets
from app.database.dependencies import get_current_user
from app.utils.flash import flash, get_flashed_messages
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/relocate")
def show_relocate_form(request: Request, user=Depends(get_current_user)):
    refs = sheets.get_reference_lists()
    location_room_map = sheets.get_location_room_map()
    flash_messages = get_flashed_messages(request)
    
    return templates.TemplateResponse("relocate.html", {
        "request": request,
        "refs": refs,
        "location_room_map": location_room_map,
        "flash_messages": flash_messages
    })

@router.post("/relocate/search")
def search_assets(
    request: Request,
    location: str = Form(...),
    room: str = Form(...),
    user=Depends(get_current_user)
):
    try:
        assets = sheets.get_assets("All")
        filtered_assets = []
        for asset in assets:
            asset_location = str(asset.get("Location", "")).strip()
            asset_room = str(asset.get("Room Location", "")).strip()
            
            if (asset_location.lower() == location.lower() and 
                asset_room.lower() == room.lower()):
                filtered_assets.append(asset)
        
        refs = sheets.get_reference_lists()
        location_room_map = sheets.get_location_room_map()
        flash_messages = get_flashed_messages(request)
        
        return templates.TemplateResponse("relocate.html", {
            "request": request,
            "refs": refs,
            "location_room_map": location_room_map,
            "flash_messages": flash_messages,
            "assets": filtered_assets,
            "current_location": location,
            "current_room": room
        })
    except Exception as e:
        flash(request, f"❌ Error searching assets: {str(e)}", "error")
        return RedirectResponse(url="/relocate", status_code=303)

@router.post("/relocate/move")
def move_asset(
    request: Request,
    asset_id: str = Form(...),
    new_location: str = Form(...),
    new_room: str = Form(...),
    notes: str = Form(""),
    user=Depends(get_current_user)
):
    try:
        # Get current assets
        assets_ws = sheets.get_worksheet("Assets")
        if not assets_ws:
            flash(request, "❌ Cannot access assets data", "error")
            return RedirectResponse(url="/relocate", status_code=303)
        
        # Find and update asset
        headers = assets_ws.row_values(1)
        data = assets_ws.get_all_values()
        
        location_col = headers.index("Location") if "Location" in headers else None
        room_col = headers.index("Room Location") if "Room Location" in headers else None
        id_col = headers.index("ID") if "ID" in headers else 0
        item_name_col = headers.index("Item Name") if "Item Name" in headers else None
        
        if location_col is None or room_col is None:
            flash(request, "❌ Cannot find location columns", "error")
            return RedirectResponse(url="/relocate", status_code=303)
        
        # Find asset row and get current data
        asset_row = None
        old_location = ""
        old_room = ""
        asset_name = ""
        
        for i, row in enumerate(data[1:], start=2):
            if len(row) > id_col and row[id_col] == asset_id:
                asset_row = i
                old_location = row[location_col] if len(row) > location_col else ""
                old_room = row[room_col] if len(row) > room_col else ""
                asset_name = row[item_name_col] if item_name_col and len(row) > item_name_col else ""
                break
        
        if asset_row:
            # Update location and room
            assets_ws.update_cell(asset_row, location_col + 1, new_location)
            assets_ws.update_cell(asset_row, room_col + 1, new_room)
            
            # Add location/room if not exists
            from app.utils.references import add_location_if_not_exists
            add_location_if_not_exists(new_location, new_room)
            
            # Log the relocation
            log_relocation(
                asset_id=asset_id,
                asset_name=asset_name,
                old_location=old_location,
                old_room=old_room,
                new_location=new_location,
                new_room=new_room,
                moved_by=user.get("username", "Unknown"),
                notes=notes
            )
            
            flash(request, f"✅ Asset {asset_id} successfully relocated to {new_location} - {new_room}", "success")
        else:
            flash(request, f"❌ Asset {asset_id} not found", "error")
            
    except Exception as e:
        flash(request, f"❌ Error relocating asset: {str(e)}", "error")
    
    return RedirectResponse(url="/relocate", status_code=303)

def log_relocation(asset_id: str, asset_name: str, old_location: str, old_room: str, 
                  new_location: str, new_room: str, moved_by: str, notes: str = ""):
    """Log relocation to Google Sheets"""
    try:
        log_ws = sheets.get_worksheet("Log_Relocation")
        if not log_ws:
            # Create sheet if doesn't exist
            sheet = sheets.get_sheet()
            log_ws = sheet.add_worksheet(title="Log_Relocation", rows=1000, cols=10)
            # Add headers
            headers = [
                "Timestamp", "Asset ID", "Asset Name", "Old Location", "Old Room",
                "New Location", "New Room", "Moved By", "Notes", "Status"
            ]
            log_ws.append_row(headers)
        
        # Add log entry
        log_entry = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            asset_id,
            asset_name,
            old_location,
            old_room,
            new_location,
            new_room,
            moved_by,
            notes,
            "Completed"
        ]
        
        log_ws.append_row(log_entry)
        
    except Exception as e:
        print(f"Error logging relocation: {e}")

@router.get("/relocate/logs")
def view_logs(request: Request, user=Depends(get_current_user)):
    """View relocation logs"""
    try:
        log_ws = sheets.get_worksheet("Log_Relocation")
        if not log_ws:
            logs = []
        else:
            logs = log_ws.get_all_records()
            # Sort by timestamp descending (newest first)
            logs = sorted(logs, key=lambda x: x.get("Timestamp", ""), reverse=True)
        
        flash_messages = get_flashed_messages(request)
        
        return templates.TemplateResponse("relocation_logs.html", {
            "request": request,
            "logs": logs,
            "flash_messages": flash_messages
        })
        
    except Exception as e:
        flash(request, f"❌ Error loading logs: {str(e)}", "error")
        return RedirectResponse(url="/relocate", status_code=303)