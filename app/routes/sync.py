# app/routes/sync.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database.dependencies import get_current_user
from app.utils.sheets import sync_assets_data
from app.utils.flash import flash

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/sync")
def show_sync_page(request: Request, user=Depends(get_current_user)):
    from app.utils.flash import get_flashed_messages
    
    flash_messages = get_flashed_messages(request)
    return templates.TemplateResponse("sync.html", {
        "request": request,
        "flash_messages": flash_messages
    })

@router.post("/sync/run")
def run_sync(request: Request, user=Depends(get_current_user)):
    try:
        result = sync_assets_data()
        if result.get("success"):
            flash(request, f"✅ {result.get('message', 'Sync berhasil!')}", "success")
        else:
            flash(request, f"❌ {result.get('message', 'Sync gagal!')}", "error")
        
        return templates.TemplateResponse("sync_result.html", {
            "request": request,
            "result": result
        })
    except Exception as e:
        flash(request, f"❌ Sync failed: {str(e)}", "error")
        return templates.TemplateResponse("sync_result.html", {
            "request": request,
            "result": {"success": False, "message": f"Sync failed: {str(e)}", "updated": 0}
        })