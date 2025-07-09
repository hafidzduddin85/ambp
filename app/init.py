# === 3. init.py ===
from fastapi import FastAPI
from app.routes import auth, asset, user, home, profile

def create_app():
    """
    Creates a FastAPI application instance.
    """
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(asset.router)
    app.include_router(user.router)
    app.include_router(home.router)
    app.include_router(profile.router)
    return app

