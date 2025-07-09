# app/routes/user.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.models import User
from app.dependencies import get_admin_user, get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/settings/users", response_class=RedirectResponse)
def redirect_users(db: Session = Depends(get_db), user: User = Depends(get_admin_user)):
    return RedirectResponse(url="/settings/users/all", status_code=303)

@router.get("/settings/users/{status}")
def users_list(request: Request, status: str, db: Session = Depends(get_db), user: User = Depends(get_admin_user)):
    users = db.query(User).filter_by(role=status).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "status": status})

@router.post("/settings/users/add")
def add_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    db: Session = Depends(get_db),
    user: User = Depends(get_admin_user)
):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username dan password tidak boleh kosong")
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="Username sudah ada")
    new_user = User(username=username, password_hash=User.hash_password(password), role=role)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/settings/users/all", status_code=303)

@router.get("/settings/users/edit/{user_id}")
def edit_user(request: Request, user_id: int, db: Session = Depends(get_db), user: User = Depends(get_admin_user)):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return templates.TemplateResponse("users_edit.html", {"request": request, "user": target, "error": None})

@router.post("/settings/users/update/{user_id}")
def update_user(
    request: Request,
    user_id: int,
    username: str = Form(...),
    password: str = Form(""),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if db.query(User).filter(User.username == username, User.id != user_id).first():
        raise HTTPException(status_code=400, detail="Username sudah digunakan")

    target.username = username
    target.role = role
    if password:
        target.password_hash = User.hash_password(password)
    db.commit()
    return RedirectResponse(url="/settings/users/all", status_code=303)

@router.get("/settings/users/delete/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(get_admin_user)):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    db.delete(target)
    db.commit()
    return RedirectResponse(url="/settings/users/all", status_code=303)

