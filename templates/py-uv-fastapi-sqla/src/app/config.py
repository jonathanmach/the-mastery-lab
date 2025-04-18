from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    sqlalchemy_database_uri: str
    connect_args: dict = {}


class Settings(BaseSettings):
    database: DatabaseSettings

