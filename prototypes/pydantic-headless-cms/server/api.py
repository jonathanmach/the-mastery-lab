from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from pydantic_cms import CMS, ContentEntry, ContentTypeSchema
from pydantic_cms.sqlite import (
    SQLiteContentRepository,
    SQLiteContentTypeRepository,
    create_schema,
)

# ---------------------------------------------------------------------------
# App-level CMS singleton (acceptable for prototype)
# ---------------------------------------------------------------------------

conn = sqlite3.connect("cms.db", check_same_thread=False)
create_schema(conn)
cms = CMS(
    content_type_repo=SQLiteContentTypeRepository(conn),
    content_repo=SQLiteContentRepository(conn),
)

app = FastAPI(title="Pydantic CMS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class EntryPayload(BaseModel):
    data: dict[str, Any]


# ---------------------------------------------------------------------------
# Content Types
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
