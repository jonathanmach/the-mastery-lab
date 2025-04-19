import pytest
from sqlalchemy import Engine
from app.config import DatabaseSettings, Settings
from app.db.models import Base
from app.db.session import get_engine, get_session
from sqlalchemy.orm import Session


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database=DatabaseSettings(
            connection_string="sqlite:///./test.db",
            connect_args={"check_same_thread": False},
        ),
    )


@pytest.fixture
def db_engine(settings: Settings):
    engine = get_engine(db_settings=settings.database)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine: Engine, settings: Settings) -> Session:
    """
    Fixture to create a database session for testing.
    """
    with get_session(db_engine) as session:
        return session
