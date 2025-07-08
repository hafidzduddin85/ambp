from app.database import SessionLocal
from app.models import User

def create_admin():
    db = SessionLocal()
    username = "admin"
    password = "admin123"

    existing = db.query(User).filter_by(username=username).first()
    if existing:
        print("❌ User 'admin' sudah ada")
        return

    admin_user = User(
        username=username,
        password_hash=User.hash_password(password),
        role="admin"
    )
    db.add(admin_user)
    db.commit()
    print("✅ Admin user berhasil dibuat")

if __name__ == "__main__":
    create_admin()
