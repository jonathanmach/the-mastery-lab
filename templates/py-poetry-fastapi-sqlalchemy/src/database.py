from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, DateTime, create_engine
from datetime import datetime

DATABASE_URL = "sqlite:///./test.db"  # Replace with your actual database URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True  # Mark this model as abstract (won't create a table for this class)

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
