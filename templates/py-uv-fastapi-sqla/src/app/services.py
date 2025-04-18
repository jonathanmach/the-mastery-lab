from app.models import User
from sqlalchemy.orm import Session


class UserService:
    db_session: Session

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_user(self, user_id: str) -> User:
        # Logic to get user details from the database
        return User(id=user_id, name="John Doe", email="email@example.com")
