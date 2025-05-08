import os
import sys

from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists

from .models import Base, engine


def create_tables():
    """Create all database tables"""
    db_url = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/slack_read_confirm")
    
    # Create the database if it doesn't exist
    if not database_exists(db_url):
        print(f"Creating database at {db_url}")
        try:
            create_database(db_url)
        except Exception as e:
            print(f"Error creating database: {e}")
            sys.exit(1)
    
    # Create tables
    print(f"Creating tables in database {db_url}")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
