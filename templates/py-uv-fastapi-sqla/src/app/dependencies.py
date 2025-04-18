from app.services import UserService


# def get_db_session(sqlalchemy_database_uri: str) -> Session:
#     engine = get_engine(sqlalchemy_database_uri)
#     db = get_session(engine)  # Replace with your actual database URI
#     with db:
#         return db
#     db.close()


def get_user_service():
    return UserService()
