from fastapi import APIRouter, HTTPException, Request

from .db import get_connection

router = APIRouter(prefix="/api/data")

ALLOWED_TABLES = {"lists", "todos"}

# Column definitions per table (excluding 'id' which is always in the path)
TABLE_COLUMNS = {
    "lists": ["name", "owner_id", "created_at"],
    "todos": ["list_id", "description", "completed", "created_at"],
}

# Columns that need int->bool conversion (SQLite has no bool, Postgres does)
BOOL_COLUMNS = {"completed"}


def _coerce_values(body: dict) -> dict:
    return {
        k: bool(v) if k in BOOL_COLUMNS and isinstance(v, int) else v
        for k, v in body.items()
    }


def _validate_table(table: str) -> None:
    if table not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Invalid table: {table}")


@router.put("/{table}/{row_id}")
async def upsert(table: str, row_id: str, request: Request):
    _validate_table(table)
    body = _coerce_values(await request.json())

    columns = [col for col in TABLE_COLUMNS[table] if col in body]
    if not columns:
        raise HTTPException(status_code=400, detail="No valid columns provided")

    all_cols = ["id"] + columns
    placeholders = ", ".join(["%s"] * len(all_cols))
    col_names = ", ".join(all_cols)
    update_set = ", ".join(f"{col} = EXCLUDED.{col}" for col in columns)

    sql = (
        f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {update_set}"
    )
    values = [row_id] + [body[col] for col in columns]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, values)

    return {"status": "ok"}


@router.patch("/{table}/{row_id}")
async def patch(table: str, row_id: str, request: Request):
    _validate_table(table)
    body = _coerce_values(await request.json())

    columns = [col for col in TABLE_COLUMNS[table] if col in body]
    if not columns:
        raise HTTPException(status_code=400, detail="No valid columns provided")

    set_clause = ", ".join(f"{col} = %s" for col in columns)
    sql = f"UPDATE {table} SET {set_clause} WHERE id = %s"
    values = [body[col] for col in columns] + [row_id]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, values)

    return {"status": "ok"}


@router.delete("/{table}/{row_id}")
async def delete(table: str, row_id: str):
    _validate_table(table)

    sql = f"DELETE FROM {table} WHERE id = %s"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [row_id])

    return {"status": "ok"}
