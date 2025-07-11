from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.utils.models import User
from app.database.dependencies import get_db, get_admin_user
from app.utils.flash import flash

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/settings/users")
def redirect_users(db: Session = Depends(get_db), user=Depends(get_admin_user)):
    return RedirectResponse(url="/settings/users/all", status_code=303)

@router.get("/settings/users/{status}")
def users_list(request: Request, status: str, db: Session = Depends(get_db), user=Depends(get_admin_user)):
    if status == "all":
        users = db.query(User).all()
    else:
        users = db.query(User).filter(User.role == status).all()

    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "status": status
    })

@router.post("/settings/users/add")
def add_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(""),
    full_name: str = Form(""),
    role: str = Form("user"),
    db: Session = Depends(get_db),
    user=Depends(get_admin_user)
):
    try:
        if not username or not password:
            flash(request, "❌ Username and password are required", "error")
            return RedirectResponse(url=f"/settings/users/all", status_code=303)
        
        if db.query(User).filter(User.username == username).first():
            flash(request, "❌ Username already exists", "error")
            return RedirectResponse(url=f"/settings/users/all", status_code=303)

        new_user = User(
            username=username,
            password_hash=User.hash_password(password),
            email=email if email else None,
            full_name=full_name if full_name else None,
            role=role
        )
        db.add(new_user)
        db.commit()
        flash(request, f"✅ User '{username}' created successfully", "success")
    except Exception as e:
        flash(request, f"❌ Error creating user: {str(e)}", "error")
        db.rollback()
    
    return RedirectResponse(url="/settings/users/all", status_code=303)

@router.get("/settings/users/edit/{user_id}")
def edit_user(request: Request, user_id: int, db: Session = Depends(get_db), user=Depends(get_admin_user)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("users_edit.html", {
        "request": request,
        "target_user": target,
        "error": None
    })

@router.post("/settings/users/update/{user_id}")
def update_user(
    request: Request,
    user_id: int,
    username: str = Form(...),
    password: str = Form(""),
    email: str = Form(""),
    full_name: str = Form(""),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    try:
        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            flash(request, "❌ User not found", "error")
            return RedirectResponse(url="/settings/users/all", status_code=303)

        # Check for duplicate username
        if db.query(User).filter(User.username == username, User.id != user_id).first():
            flash(request, "❌ Username already exists", "error")
            return RedirectResponse(url=f"/settings/users/edit/{user_id}", status_code=303)

        target.username = username
        target.email = email if email else None
        target.full_name = full_name if full_name else None
        target.role = role
        if password:
            target.password_hash = User.hash_password(password)
        
        db.commit()
        flash(request, f"✅ User '{username}' updated successfully", "success")
    except Exception as e:
        flash(request, f"❌ Error updating user: {str(e)}", "error")
        db.rollback()
    
    return RedirectResponse(url="/settings/users/all", status_code=303)

@router.get("/settings/users/delete/{user_id}")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db), user=Depends(get_admin_user)):
    try:
        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            flash(request, "❌ User not found", "error")
            return RedirectResponse(url="/settings/users/all", status_code=303)
        
        username = target.username
        db.delete(target)
        db.commit()
        flash(request, f"✅ User '{username}' deleted successfully", "success")
    except Exception as e:
        flash(request, f"❌ Error deleting user: {str(e)}", "error")
        db.rollback()
    
    return RedirectResponse(url="/settings/users/all", status_code=303)

@router.get("/settings/users/reset/{user_id}")
def reset_password(request: Request, user_id: int, db: Session = Depends(get_db), user=Depends(get_admin_user)):
    try:
        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            flash(request, "❌ User not found", "error")
            return RedirectResponse(url="/settings/users/all", status_code=303)

        default_password = "123456"
        target.password_hash = User.hash_password(default_password)
        db.commit()
        flash(request, f"✅ Password reset for '{target.username}' (new password: {default_password})", "success")
    except Exception as e:
        flash(request, f"❌ Error resetting password: {str(e)}", "error")
        db.rollback()
    
    return RedirectResponse(url="/settings/users/all", status_code=303)