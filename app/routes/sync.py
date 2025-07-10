from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.database.dependencies import get_current_user
from app.utils.sheets import sync_assets_data
from app.utils.flash import flash, get_flashed_messages

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/sync")
def sync_page(request: Request, user=Depends(get_current_user)):
    """Tampilkan halaman sync"""
    flash_messages = get_flashed_messages(request)
    return templates.TemplateResponse("sync.html", {
        "request": request,
        "flash_messages": flash_messages
    })


@router.get("/sync-assets")
def sync_page_alt(request: Request, user=Depends(get_current_user)):
    """Alias URL ke halaman sync"""
    return sync_page(request, user)


@router.post("/sync/run")
def run_sync_process(request: Request, user=Depends(get_current_user)):
    """Jalankan proses sync aset"""
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
            "result": {
                "success": False,
                "message": f"Sync failed: {str(e)}",
                "updated": 0
            }
        })
