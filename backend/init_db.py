"""
Script to initialize the database using SQLAlchemy models.
Run this after setting up the database with the SQL scripts.
"""

from app.db.database import engine, Base
from app.models.models import (
    User, Package, UserPackage, Section, Question,
    Test, TestQuestion, TestAttempt, QuestionAttempt
)

def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()

