from app.database.database import Base, engine
from app.utils.models import User

from sqlalchemy import inspect

def init_db():
    try:
        inspector = inspect(engine)
        # Create all tables if User table does not exist
        if not inspector.has_table(User.__tablename__):
            Base.metadata.create_all(bind=engine)
            print("Database tables created.")
        else:
            print("Database tables already exist.")
    except Exception as e:
        print(f"An error occurred while creating database tables: {e}")

if __name__ == "__main__":
    init_db()

