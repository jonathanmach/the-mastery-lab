from typing import Annotated

from fastapi import Depends
from app.config import DatabaseSettings, Settings
from app.db.session import get_engine, get_session
from app.services import UserService
from sqlalchemy.orm import Session


def get_config() -> Settings:
    # TODO: Implement a function to load configuration from environment variables or a config file
    return Settings(
        database=DatabaseSettings(
            sqlalchemy_database_uri="sqlite:///./app.db",
            connect_args={"check_same_thread": False},
        ),
    )


def get_db_session(config: Annotated[Settings, Depends(get_config)]) -> Session:
    engine = get_engine(config.database)
    return get_session(engine)


DBSessionDep = Annotated[Session, Depends(get_db_session)]


def get_user_service(db_session: DBSessionDep) -> UserService:
    return UserService(db_session=db_session)
