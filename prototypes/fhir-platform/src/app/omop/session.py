from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.omop.models import Base


def get_omop_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True)


def init_omop_db(database_url: str, overwrite: bool = False) -> None:
    """Create all OMOP CDM tables. Pass overwrite=True to drop and recreate."""
    engine = get_omop_engine(database_url)
    if overwrite:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@contextmanager
def get_omop_session(database_url: str) -> Generator[Session, None, None]:
    engine = get_omop_engine(database_url)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
