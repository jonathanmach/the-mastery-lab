from __future__ import annotations

import json
import sqlite3

from .models import ContentEntry, ContentTypeSchema
from .repository import ContentRepository, ContentTypeRepository


_DDL = """
CREATE TABLE IF NOT EXISTS content_types (
    id     TEXT PRIMARY KEY,
    schema TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content (
    id               TEXT PRIMARY KEY,
    content_type_id  TEXT NOT NULL,
    data             TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_content_by_type ON content(content_type_id);
"""


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_DDL)
    conn.commit()


class SQLiteContentTypeRepository(ContentTypeRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, schema: ContentTypeSchema) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO content_types (id, schema) VALUES (?, ?)",
            (schema.id, schema.model_dump_json()),
        )
        self._conn.commit()

    def get(self, id: str) -> ContentTypeSchema | None:
        row = self._conn.execute(
            "SELECT schema FROM content_types WHERE id = ?", (id,)
        ).fetchone()
        return ContentTypeSchema.model_validate_json(row[0]) if row else None

    def list_all(self) -> list[ContentTypeSchema]:
        rows = self._conn.execute("SELECT schema FROM content_types").fetchall()
        return [ContentTypeSchema.model_validate_json(row[0]) for row in rows if row[0] is not None]

    def delete(self, id: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM content_types WHERE id = ?", (id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def exists(self, id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM content_types WHERE id = ?", (id,)
        ).fetchone()
        return row is not None


class SQLiteContentRepository(ContentRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, entry: ContentEntry) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO content (id, content_type_id, data) VALUES (?, ?, ?)",
            (entry.id, entry.content_type_id, json.dumps(entry.data)),
        )
        self._conn.commit()

    def get(self, id: str) -> ContentEntry | None:
        row = self._conn.execute(
            "SELECT id, content_type_id, data FROM content WHERE id = ?", (id,)
        ).fetchone()
        if row is None:
            return None
        return ContentEntry(id=row[0], content_type_id=row[1], data=json.loads(row[2]))

    def list_all(self, content_type_id: str) -> list[ContentEntry]:
        rows = self._conn.execute(
            "SELECT id, content_type_id, data FROM content WHERE content_type_id = ?",
            (content_type_id,),
        ).fetchall()
        return [
            ContentEntry(id=row[0], content_type_id=row[1], data=json.loads(row[2]))
            for row in rows
        ]

    def delete(self, id: str) -> bool:
        cursor = self._conn.execute("DELETE FROM content WHERE id = ?", (id,))
        self._conn.commit()
        return cursor.rowcount > 0


