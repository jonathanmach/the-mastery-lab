from __future__ import annotations

import sqlite3

import pytest

from pydantic_cms.cms import CMS
from pydantic_cms.field_types import FieldDefinition, FieldType
from pydantic_cms.models import ContentTypeSchema
from pydantic_cms.repository import ContentRepository, ContentTypeRepository
from pydantic_cms.sqlite import (
    SQLiteContentRepository,
    SQLiteContentTypeRepository,
    create_schema,
)


@pytest.fixture
def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    return conn


@pytest.fixture
def content_type_repo(db_conn: sqlite3.Connection) -> ContentTypeRepository:
    return SQLiteContentTypeRepository(db_conn)


@pytest.fixture
def content_repo(db_conn: sqlite3.Connection) -> ContentRepository:
    return SQLiteContentRepository(db_conn)


@pytest.fixture
def cms(
    content_type_repo: ContentTypeRepository,
    content_repo: ContentRepository,
) -> CMS:
    return CMS(content_type_repo=content_type_repo, content_repo=content_repo)


@pytest.fixture
def blog_post_schema() -> ContentTypeSchema:
    return ContentTypeSchema(
        id="blog-post",
        name="Blog Post",
        fields=[
            FieldDefinition(name="title", type=FieldType.text, required=True),
            FieldDefinition(name="body", type=FieldType.rich_text, required=True),
            FieldDefinition(name="view_count", type=FieldType.integer, required=False),
            FieldDefinition(
                name="tags",
                type=FieldType.list_,
                required=False,
                item_type=FieldType.text,
            ),
        ],
    )
