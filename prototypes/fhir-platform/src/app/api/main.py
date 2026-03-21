from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="FHIR Platform BFF",
    description="Backend-for-frontend for the FHIR Platform prototype",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/patients", tags=["patients"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
