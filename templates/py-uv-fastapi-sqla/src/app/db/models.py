from sqlalchemy import Column, String

from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default="UUID()")
    email = Column(String, unique=True, index=True)
    name = Column(String)
