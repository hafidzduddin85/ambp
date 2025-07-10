# === 3. init.py ===
from fastapi import FastAPI
from app.routes import auth, asset, user, home, profile, sync, relocation, init_add

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
    app.include_router(sync.router)
    app.include_router(relocation.router)
    app.include_router(init_add.router)
    return app

