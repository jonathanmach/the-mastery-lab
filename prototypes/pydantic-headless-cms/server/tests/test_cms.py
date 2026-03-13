from __future__ import annotations

import pytest
from pydantic import ValidationError

from pydantic_cms.cms import CMS
from pydantic_cms.field_types import FieldDefinition, FieldType
from pydantic_cms.models import ContentEntry, ContentTypeSchema


# ── Content Type CRUD ────────────────────────────────────────────────────────

def test_define_and_get_content_type(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    retrieved = cms.get_content_type("blog-post")
    assert retrieved.name == "Blog Post"
    assert len(retrieved.fields) == 4


def test_get_unknown_content_type_raises(cms: CMS) -> None:
    with pytest.raises(KeyError):
        cms.get_content_type("nonexistent")


def test_list_content_types(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    cms.define_content_type(ContentTypeSchema(id="recipe", name="Recipe", fields=[]))
    types = cms.list_content_types()
    assert len(types) == 2


def test_update_content_type(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    updated = ContentTypeSchema(
        id="blog-post",
        name="Updated Blog Post",
        fields=blog_post_schema.fields,
    )
    cms.update_content_type(updated)
    assert cms.get_content_type("blog-post").name == "Updated Blog Post"


def test_update_nonexistent_content_type_raises(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    with pytest.raises(KeyError):
        cms.update_content_type(blog_post_schema)


def test_delete_content_type(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    cms.delete_content_type("blog-post")
    with pytest.raises(KeyError):
        cms.get_content_type("blog-post")


def test_delete_nonexistent_content_type_raises(cms: CMS) -> None:
    with pytest.raises(KeyError):
        cms.delete_content_type("nonexistent")


# ── Content CRUD ─────────────────────────────────────────────────────────────

def test_create_content_returns_entry(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    entry = cms.create_content("blog-post", {"title": "Hello", "body": "<p>Hi</p>"})
    assert isinstance(entry, ContentEntry)
    assert entry.id is not None
    assert entry.content_type_id == "blog-post"
    assert entry.data["title"] == "Hello"


def test_create_content_missing_required_field_raises(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    with pytest.raises(ValidationError):
        cms.create_content("blog-post", {"body": "Missing title"})


def test_create_content_unknown_type_raises(cms: CMS) -> None:
    with pytest.raises(KeyError):
        cms.create_content("nonexistent", {"title": "Hi"})


def test_create_content_with_optional_fields(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    entry = cms.create_content(
        "blog-post",
        {"title": "Hi", "body": "Body", "tags": ["a", "b"], "view_count": 10},
    )
    assert entry.data["tags"] == ["a", "b"]
    assert entry.data["view_count"] == 10


def test_get_content(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    entry = cms.create_content("blog-post", {"title": "Hi", "body": "Body"})
    retrieved = cms.get_content(entry.id)
    assert retrieved.data["title"] == "Hi"


def test_get_content_unknown_raises(cms: CMS) -> None:
    with pytest.raises(KeyError):
        cms.get_content("nonexistent-id")


def test_list_content(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    cms.create_content("blog-post", {"title": "A", "body": "A"})
    cms.create_content("blog-post", {"title": "B", "body": "B"})
    entries = cms.list_content("blog-post")
    assert len(entries) == 2


def test_list_content_empty(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    assert cms.list_content("blog-post") == []


def test_update_content(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    entry = cms.create_content("blog-post", {"title": "Old", "body": "Old body"})
    updated = cms.update_content(entry.id, {"title": "New", "body": "New body"})
    assert updated.data["title"] == "New"
    assert updated.id == entry.id


def test_update_content_invalid_data_raises(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    entry = cms.create_content("blog-post", {"title": "Old", "body": "Old body"})
    with pytest.raises(ValidationError):
        cms.update_content(entry.id, {"body": "Missing title"})


def test_update_content_unknown_raises(cms: CMS) -> None:
    with pytest.raises(KeyError):
        cms.update_content("nonexistent-id", {"title": "Hi"})


def test_delete_content(cms: CMS, blog_post_schema: ContentTypeSchema) -> None:
    cms.define_content_type(blog_post_schema)
    entry = cms.create_content("blog-post", {"title": "Gone", "body": "Gone"})
    cms.delete_content(entry.id)
    with pytest.raises(KeyError):
        cms.get_content(entry.id)


def test_delete_content_unknown_raises(cms: CMS) -> None:
    with pytest.raises(KeyError):
        cms.delete_content("nonexistent-id")
