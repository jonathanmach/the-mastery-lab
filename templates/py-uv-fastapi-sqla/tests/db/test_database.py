from sqlalchemy.orm import Session
from app.db.models import User


def test_db_session_fixture(db_session):
    assert db_session is not None
    assert isinstance(db_session, Session)


def test_db_operations(db_session: Session):
    user = User(name="testuser", email="email@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.id is not None
