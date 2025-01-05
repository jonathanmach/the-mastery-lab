from sqlalchemy import Column, String, Text
from src.database import BaseModel


class ExampleModel(BaseModel):
    __tablename__ = "example_model"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
