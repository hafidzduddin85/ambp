# === 4. main.py ===
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.sessions import SessionMiddleware
from fastapi.responses import FileResponse
from app.init import create_app
from app.config import SESSION_SECRET

app = create_app()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
import os
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

def favicon():
    import os
    favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")
    return FileResponse(favicon_path)
    return FileResponse("app/static/favicon.ico")
