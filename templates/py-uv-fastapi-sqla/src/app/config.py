from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    connection_string: str
    connect_args: dict = {}


class Settings(BaseSettings):
    database: DatabaseSettings

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in the environment variables

