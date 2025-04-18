from app.models import User


class UserService:
    def get_user(self, user_id: str) -> User:
        # Logic to get user details from the database
        return User(id=user_id, name="John Doe", email="email@example.com")
