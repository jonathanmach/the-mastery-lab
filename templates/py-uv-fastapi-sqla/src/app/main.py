from fastapi import Depends, FastAPI

from app.dependencies import get_user_service
from app.models import User
from app.services import UserService

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/users/{user_id}")
async def get_user(user_id: str, user_service: UserService = Depends(get_user_service)) -> User:
    user = user_service.get_user(user_id)
    return user
