from sqlalchemy import Column, String
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default="UUID()")
    email = Column(String, unique=True, index=True)
    name = Column(String)
