# app/init.py

from fastapi import FastAPI
from app.routes import (
    auth,
    asset,
    assets,
    user,
    home,
    profile,
    sync,
    relocation,
    setup_admin,
    reset_db
)

def create_app() -> FastAPI:
    """
    Creates and configures a FastAPI application instance.
    """
    app = FastAPI()

    # Register all routers
    app.include_router(auth.router)
    app.include_router(asset.router)
    app.include_router(assets.router)
    app.include_router(user.router)
    app.include_router(home.router)
    app.include_router(profile.router)
    app.include_router(sync.router)
    app.include_router(relocation.router)
    app.include_router(setup_admin.router)
    app.include_router(reset_db.router)

    return app
