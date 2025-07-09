# app/routes/user.py
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.models import User
from app.dependencies import get_admin_user, get_db

router = APIRouter()

@router.get("/settings/users", response_class=HTMLResponse)
def manage_users(request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin_user)):
    users = db.query(User).all()
    return HTMLResponse(template_name="users.html", context={"request": request, "users": users})

@router.post("/settings/users/add")
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

@router.get("/settings/users/edit/{user_id}", response_class=HTMLResponse)
def edit_user(request: Request, user_id: int, db: Session = Depends(get_db), user: User = Depends(get_admin_user)):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return HTMLResponse(template_name="users_edit.html", context={"request": request, "user": target, "error": None})

@router.post("/settings/users/update/{user_id}", response_class=HTMLResponse)
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
        return HTMLResponse(template_name="users_edit.html", context={"request": request, "user": target, "error": "Username sudah digunakan"})

    target.username = username
    target.role = role
    if password:
        target.password_hash = User.hash_password(password)
    db.commit()
    return RedirectResponse(url="/settings/users", status_code=303)

@router.get("/settings/users/delete/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(get_admin_user)):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    db.delete(target)
    db.commit()
    return RedirectResponse(url="/settings/users", status_code=303)
