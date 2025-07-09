# === 3. init.py ===
from fastapi import FastAPI
from app.routes import auth, asset, user

def create_app():
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(asset.router)
    app.include_router(user.router)
    return app