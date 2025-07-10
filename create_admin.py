#!/usr/bin/env python3
"""
Script to create admin user and initialize database
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import init_db, SessionLocal
from app.utils.models import User

def create_admin_user():
    """Create default admin user"""
    db = SessionLocal()
    try:
        # Initialize database tables
        init_db()
        
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            password_hash=User.hash_password("admin123"),
            email="admin@example.com",
            full_name="System Administrator",
            role="admin",
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        print("✅ Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("⚠️  Please change the default password after first login")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()