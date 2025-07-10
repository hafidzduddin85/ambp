# app/routes/relocation.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils import sheets
from app.database.dependencies import get_current_user
from app.utils.flash import flash, get_flashed_messages

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
        filtered_assets = [
            asset for asset in assets 
            if asset.get("Location", "").lower() == location.lower() 
            and asset.get("Room Location", "").lower() == room.lower()
        ]
        
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
        
        if location_col is None or room_col is None:
            flash(request, "❌ Cannot find location columns", "error")
            return RedirectResponse(url="/relocate", status_code=303)
        
        # Find asset row
        asset_row = None
        for i, row in enumerate(data[1:], start=2):  # Start from row 2 (skip header)
            if len(row) > id_col and row[id_col] == asset_id:
                asset_row = i
                break
        
        if asset_row:
            # Update location and room
            assets_ws.update_cell(asset_row, location_col + 1, new_location)
            assets_ws.update_cell(asset_row, room_col + 1, new_room)
            
            # Add location/room if not exists
            sheets.add_location_if_not_exists(new_location, new_room)
            
            flash(request, f"✅ Asset {asset_id} successfully relocated to {new_location} - {new_room}", "success")
        else:
            flash(request, f"❌ Asset {asset_id} not found", "error")
            
    except Exception as e:
        flash(request, f"❌ Error relocating asset: {str(e)}", "error")
    
    return RedirectResponse(url="/relocate", status_code=303)