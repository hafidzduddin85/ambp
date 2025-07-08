# migrate_users_add_role.py

from sqlalchemy import create_engine, text
import os

# Gunakan DATABASE_URL dari environment variable, atau fallback lokal
DATABASE_URL = os.getenv("DATABASE_URL")

# Buat koneksi ke database
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        # Eksekusi SQL untuk menambahkan kolom 'role' ke tabel users
        conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user';"))
        print("✅ Kolom 'role' berhasil ditambahkan ke tabel 'users'.")
    except Exception as e:
        print("❌ Gagal menambahkan kolom 'role':", e)
