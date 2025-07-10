# app/routes/sync.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database.dependencies import get_current_user
from app.utils.sheets import sync_assets_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/sync")
def show_sync_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("sync.html", {
        "request": request
    })

@router.post("/sync/run")
def run_sync(request: Request, user=Depends(get_current_user)):
    try:
        result = sync_assets_data()
        return templates.TemplateResponse("sync_result.html", {
            "request": request,
            "result": result
        })
    except Exception as e:
        return templates.TemplateResponse("sync_result.html", {
            "request": request,
            "result": {"success": False, "message": f"Sync failed: {str(e)}", "updated": 0}
        })