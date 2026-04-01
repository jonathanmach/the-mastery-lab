"""
One-off migration: export content type schemas from SQLite → YAML Schema files.

Run from the server/ directory:
    python migrate_schemas.py [--schemas-dir ../schemas] [--db .storage/cms.db]
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

# Ensure pydantic_cms is importable when run from server/
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pydantic_cms.sqlite import SQLiteContentTypeRepository
from pydantic_cms.fs_repository import _content_type_to_json_schema, FileSystemSchemaRepository


def migrate(db_path: Path, schemas_dir: Path) -> None:
    if not db_path.exists():
        print(f"Database not found at {db_path}, nothing to migrate.")
        return

    conn = sqlite3.connect(str(db_path))
    sqlite_repo = SQLiteContentTypeRepository(conn)
    fs_repo = FileSystemSchemaRepository(schemas_dir)

    schemas = sqlite_repo.list_all()
    if not schemas:
        print("No content types found in SQLite database.")
        return

    for schema in schemas:
        out_path = schemas_dir / f"{schema.id}.schema.yml"
        if out_path.exists():
            print(f"  SKIP  {schema.id} (file already exists)")
            continue
        fs_repo.save(schema)
        print(f"  WROTE {out_path}")

    conn.close()
    print(f"\nMigrated {len(schemas)} schema(s) to {schemas_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate SQLite schemas to YAML Schema files")
    parser.add_argument("--schemas-dir", default="../schemas", type=Path)
    parser.add_argument("--db", default=".storage/cms.db", type=Path)
    args = parser.parse_args()

    migrate(args.db, args.schemas_dir)
