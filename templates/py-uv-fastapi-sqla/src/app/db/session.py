from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

from app.config import DatabaseSettings


def get_engine(db_settings: DatabaseSettings) -> Engine:
    return create_engine(
        db_settings.connection_string,
        connect_args=db_settings.connect_args,
    )


def get_session(engine: Engine) -> Session:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
