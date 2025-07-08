from fastapi import FastAPI, Request, Form, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from itsdangerous import URLSafeSerializer
import os, csv
from io import StringIO

from app import sheets
from app.models import User
from app.database import SessionLocal

app = FastAPI()

# Session Middleware
SESSION_SECRET = os.getenv("SESSION_SECRET", "supersecret")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
serializer = URLSafeSerializer(SESSION_SECRET)

# Static & Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# === DB Dependency ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Auth Dependency ===
def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return user

def get_admin_user(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    user = db.query(User).filter_by(username=username).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    return user

# === Routes ===
@app.get("/", response_class=HTMLResponse)
def root_redirect():
    return RedirectResponse(url="/home")

@app.get("/home", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        return RedirectResponse("/login")

    user = db.query(User).filter_by(username=username).first()
    return templates.TemplateResponse("home.html", {"request": request, "user": user})
   
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/login")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Username atau password salah"})
    request.session["user"] = user.username
    return RedirectResponse(url="/home", status_code=302)

@app.api_route("/logout", methods=["GET", "POST"])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
    
@app.get("/input", response_class=HTMLResponse)
def show_form(request: Request, user: str = Depends(get_current_user)):
    refs = sheets.get_reference_lists()
    location_room_map = sheets.get_location_room_map()
    return templates.TemplateResponse("input_form.html", {
        "request": request,
        "refs": refs,
        "location_room_map": location_room_map
    })

@app.post("/submit")
def submit_asset(
    request: Request,
    item_name: str = Form(...),
    category: str = Form(...),
    type: str = Form(...),
    manufacture: str = Form(""),
    model: str = Form(""),
    serial_number: str = Form(""),
    company: str = Form(...),
    code_company: str = Form(""),
    bisnis_unit: str = Form(""),
    location: str = Form(...),
    room_location: str = Form(...),
    notes: str = Form(""),
    condition: str = Form(""),
    purchase_date: str = Form(""),
    purchase_cost: str = Form(""),
    warranty: str = Form("No"),
    supplier: str = Form(""),
    journal: str = Form(""),
    owner: str = Form(...),
    user: str = Depends(get_current_user)
):
    sheets.add_type_if_not_exists(type, category)
    sheets.add_location_if_not_exists(location, room_location)
    sheets.add_company_with_code_if_not_exists(company, code_company)
    sheets.add_owner_if_not_exists(owner)
    sheets.add_category_if_not_exists(category)

    data = {
        "item_name": item_name,
        "category": category,
        "type": type,
        "manufacture": manufacture,
        "model": model,
        "serial_number": serial_number,
        "company": company,
        "code_company": code_company,
        "bisnis_unit": bisnis_unit,
        "location": location,
        "room_location": room_location,
        "notes": notes,
        "condition": condition,
        "purchase_date": purchase_date,
        "purchase_cost": purchase_cost,
        "warranty": warranty,
        "supplier": supplier,
        "journal": journal,
        "owner": owner
    }

    sheets.append_asset(data)
    return RedirectResponse(url="/input", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, status: str = "All", user: str = Depends(get_current_user)):
    data = sheets.get_assets(status)
    kategori_summary, tahun_summary = {}, {}

    for row in data:
        kategori = row.get("Category", "Lainnya")
        kategori_summary[kategori] = kategori_summary.get(kategori, 0) + 1
        tahun = str(row.get("Tahun", ""))
        if tahun:
            tahun_summary[tahun] = tahun_summary.get(tahun, 0) + 1

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "selected_status": status,
        "assets": data,
        "kategori_labels": list(kategori_summary.keys()),
        "kategori_values": list(kategori_summary.values()),
        "tahun_labels": list(tahun_summary.keys()),
        "tahun_values": list(tahun_summary.values()),
    })

@app.get("/export")
def export_excel(status: str = "All", user: str = Depends(get_current_user)):
    data = sheets.get_assets(status)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=assets_{status}.csv"}
    )

# ===========================
# ✅ Admin - Manage Users
# ===========================
@app.get("/settings/users", response_class=HTMLResponse)
def manage_users(request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin_user)):
    users = db.query(User).all()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users
    })

@app.post("/settings/users/add")
def add_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    db: Session = Depends(get_db),
    user: User = Depends(get_admin_user)
):
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="Username sudah ada")
    new_user = User(username=username, password_hash=User.hash_password(password), role=role)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/settings/users", status_code=303)
    
 @app.get("/init-admin", include_in_schema=False)
def init_admin(db: Session = Depends(get_db)):
    # Update user 'admin' ke role admin
    user = db.query(User).filter_by(username="admin").first()
    if user:
        user.role = "admin"
        db.commit()
        return {"message": "✅ Role user 'admin' diubah menjadi 'admin'"}
    return {"message": "❌ User 'admin' tidak ditemukan"}

@app.get("/add-user", include_in_schema=False)
def add_user(db: Session = Depends(get_db)):
    # Tambah user baru
    username = "operator"
    password = "operator123"
    role = "user"

    if db.query(User).filter_by(username=username).first():
        return {"message": f"⚠️ User '{username}' sudah ada"}

    new_user = User(
        username=username,
        password_hash=User.hash_password(password),
        role=role
    )
    db.add(new_user)
    db.commit()
    return {"message": f"✅ User '{username}' berhasil ditambahkan"}
   

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("app/static/favicon.ico")

# Uvicorn
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
