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
        flash(request, f"❌ Gagal mencari aset: {str(e)}", "error")
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
        success, message = sheets.update_asset_location(asset_id, new_location, new_room)
        if success:
            flash(request, f"✅ {message}", "success")
        else:
            flash(request, f"❌ {message}", "error")
    except Exception as e:
        flash(request, f"❌ Gagal memindahkan aset: {str(e)}", "error")

    return RedirectResponse(url="/relocate", status_code=303)
