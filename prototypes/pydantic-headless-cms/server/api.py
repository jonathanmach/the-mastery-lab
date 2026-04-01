from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from pydantic_cms import CMS, ContentEntry, ContentTypeSchema, LocalObjectStorage, ObjectStorage
from pydantic_cms.fs_repository import FileSystemSchemaRepository
from pydantic_cms.schema_loader import ResolvedSchema, SchemaLoader
from pydantic_cms.sqlite import SQLiteContentRepository, create_schema
import sqlite3

# ---------------------------------------------------------------------------
# App-level singletons (acceptable for prototype)
# ---------------------------------------------------------------------------

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
SCHEMAS_DIR.mkdir(exist_ok=True)

Path(".storage").mkdir(exist_ok=True)
conn = sqlite3.connect(".storage/cms.db", check_same_thread=False)
create_schema(conn)

schema_repo = FileSystemSchemaRepository(SCHEMAS_DIR)
loader = SchemaLoader(SCHEMAS_DIR)

cms = CMS(
    content_type_repo=schema_repo,
    content_repo=SQLiteContentRepository(conn),
)
storage: ObjectStorage = LocalObjectStorage()

app = FastAPI(title="Pydantic CMS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=".storage/uploads", html=False), name="media")

# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class EntryPayload(BaseModel):
    data: dict[str, Any]


class RawSchemaPayload(BaseModel):
    schema_: dict[str, Any]

    class Config:
        populate_by_name = True


# ---------------------------------------------------------------------------
# Object Storage
# ---------------------------------------------------------------------------


@app.post("/api/upload")
async def upload_file(file: UploadFile) -> dict[str, str]:
    suffix = Path(file.filename or "file").suffix
    key = f"{uuid.uuid4()}{suffix}"
    url = storage.upload(key, await file.read(), file.content_type or "application/octet-stream")
    return {"key": key, "url": url}


# ---------------------------------------------------------------------------
# JSON Schema endpoints
# ---------------------------------------------------------------------------


@app.get("/api/schemas")
def list_schemas() -> list[dict[str, str]]:
    """List all schema IDs and titles."""
    result = []
    for schema_id in loader.list_ids():
        try:
            raw = loader.load_raw(schema_id)
            result.append({"id": schema_id, "title": raw.get("title", schema_id)})
        except Exception:
            pass
    return result


@app.get("/api/schemas/{schema_id}/raw")
def get_schema_raw(schema_id: str) -> dict:
    """Return the raw JSON Schema file."""
    try:
        return loader.load_raw(schema_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/schemas/{schema_id}/resolved")
def get_schema_resolved(schema_id: str) -> dict:
    """
    Return a resolved schema with own_fields and inherited_fields separated.
    Used by the admin field-builder UI.
    """
    try:
        resolved = loader.resolve(schema_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "id": resolved.id,
        "name": resolved.name,
        "base": resolved.base,
        "own_fields": [f.model_dump() for f in resolved.own_fields],
        "inherited_fields": [f.model_dump() for f in resolved.inherited_fields],
    }


@app.put("/api/schemas/{schema_id}", status_code=200)
def save_schema_raw(schema_id: str, payload: dict[str, Any]) -> dict:
    """Write a raw JSON Schema dict to disk."""
    schema_repo.save_raw(schema_id, payload)
    return {"id": schema_id, "status": "saved"}


@app.delete("/api/schemas/{schema_id}", status_code=204)
def delete_schema(schema_id: str) -> None:
    if not schema_repo.delete(schema_id):
        raise HTTPException(status_code=404, detail=f"Schema '{schema_id}' not found")


# ---------------------------------------------------------------------------
# Content Types (field-builder API — backed by FileSystemSchemaRepository)
# ---------------------------------------------------------------------------


@app.get("/api/content-types", response_model=list[ContentTypeSchema])
def list_content_types() -> list[ContentTypeSchema]:
    return cms.list_content_types()


@app.post("/api/content-types", response_model=ContentTypeSchema, status_code=201)
def create_content_type(schema: ContentTypeSchema) -> ContentTypeSchema:
    return cms.define_content_type(schema)


@app.get("/api/content-types/{id}", response_model=ContentTypeSchema)
def get_content_type(id: str) -> ContentTypeSchema:
    try:
        return cms.get_content_type(id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/api/content-types/{id}", response_model=ContentTypeSchema)
def update_content_type(id: str, schema: ContentTypeSchema) -> ContentTypeSchema:
    try:
        return cms.update_content_type(schema)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/content-types/{id}", status_code=204)
def delete_content_type(id: str) -> None:
    try:
        cms.delete_content_type(id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Content Entries
# ---------------------------------------------------------------------------


@app.get("/api/entries", response_model=list[ContentEntry])
def list_all_entries() -> list[ContentEntry]:
    entries: list[ContentEntry] = []
    for ct in cms.list_content_types():
        entries.extend(cms.list_content(ct.id))
    return entries


@app.get(
    "/api/content-types/{type_id}/entries", response_model=list[ContentEntry]
)
def list_entries(type_id: str) -> list[ContentEntry]:
    try:
        cms.get_content_type(type_id)  # validate type exists
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return cms.list_content(type_id)


@app.post(
    "/api/content-types/{type_id}/entries",
    response_model=ContentEntry,
    status_code=201,
)
def create_entry(type_id: str, payload: EntryPayload) -> ContentEntry:
    try:
        return cms.create_content(type_id, payload.data)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


@app.get("/api/entries/{id}", response_model=ContentEntry)
def get_entry(id: str) -> ContentEntry:
    try:
        return cms.get_content(id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/api/entries/{id}", response_model=ContentEntry)
def update_entry(id: str, payload: EntryPayload) -> ContentEntry:
    try:
        return cms.update_content(id, payload.data)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


@app.delete("/api/entries/{id}", status_code=204)
def delete_entry(id: str) -> None:
    try:
        cms.delete_content(id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Public API (read-only)
# ---------------------------------------------------------------------------


@app.get("/public/content-types/{type_id}/entries", response_model=list[ContentEntry])
def public_list_entries(type_id: str) -> list[ContentEntry]:
    try:
        cms.get_content_type(type_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return cms.list_content(type_id)


@app.get("/public/entries/{id}", response_model=ContentEntry)
def public_get_entry(id: str) -> ContentEntry:
    try:
        return cms.get_content(id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
