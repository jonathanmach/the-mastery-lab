import sqlite3

from pydantic_cms import CMS
from pydantic_cms.sqlite import SQLiteContentRepository, SQLiteContentTypeRepository, create_schema


def create_cms(db_path: str = ":memory:") -> CMS:
    conn = sqlite3.connect(db_path)
    create_schema(conn)
    return CMS(
        content_type_repo=SQLiteContentTypeRepository(conn),
        content_repo=SQLiteContentRepository(conn),
    )


def main() -> None:
    cms = create_cms()
    print(cms)


if __name__ == "__main__":
    main()
