from __future__ import annotations

import pytest

from pydantic_cms.cms import CMS
from pydantic_cms.field_types import FieldDefinition, FieldType
from pydantic_cms.models import ContentTypeSchema
from pydantic_cms.repository import InMemoryContentRepository, InMemoryContentTypeRepository


@pytest.fixture
def content_type_repo() -> InMemoryContentTypeRepository:
    return InMemoryContentTypeRepository()


@pytest.fixture
def content_repo() -> InMemoryContentRepository:
    return InMemoryContentRepository()


@pytest.fixture
def cms(
    content_type_repo: InMemoryContentTypeRepository,
    content_repo: InMemoryContentRepository,
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
