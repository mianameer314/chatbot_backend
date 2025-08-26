from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_light_migrations():
    ddl = """
    ALTER TABLE chat_messages
        ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(20),
        ADD COLUMN IF NOT EXISTS sentiment_score DOUBLE PRECISION,
        ADD COLUMN IF NOT EXISTS tone VARCHAR(20);
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))
