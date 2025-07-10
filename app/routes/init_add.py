from fastapi import APIRouter, Request, Depends
from sqlalchemy import text, inspect
from app.database.database import engine
from app.database.dependencies import get_admin_user
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/init-add", response_class=HTMLResponse)
def add_missing_columns(request: Request, user=Depends(get_admin_user)):
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns("users")
        column_names = [col["name"] for col in columns]

        statements = []
        with engine.connect() as conn:
            if "hashed_password" not in column_names:
                conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR;"))
                statements.append("✅ Added column: hashed_password")

            if "role" not in column_names:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user';"))
                statements.append("✅ Added column: role")

            if "is_active" not in column_names:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active VARCHAR DEFAULT 'true';"))
                statements.append("✅ Added column: is_active")

        if not statements:
            return "<h3>✅ All columns already exist in `users` table.</h3>"
        return "<br>".join(statements)

    except Exception as e:
        return f"<h3>❌ Error: {str(e)}</h3>"
