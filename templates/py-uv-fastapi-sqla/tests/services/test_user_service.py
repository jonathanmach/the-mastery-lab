from app.services import UserService


class TestUserService:
    def test_get_user(self):
        # Arrange
        user_service = UserService()
        user = user_service.get_user("12345")

        # Assert
        assert user.id == "12345"
        assert user.name == "John Doe"
        assert user.email is not None
