from fastapi import FastAPI

from .auth import router as auth_router
from .crud import router as crud_router

app = FastAPI(title="PowerSync Demo Backend")

app.include_router(auth_router)
app.include_router(crud_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
