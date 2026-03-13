from __future__ import annotations

import pytest

from pydantic_cms.field_types import FieldDefinition, FieldType
from pydantic_cms.models import ContentEntry, ContentTypeSchema
from pydantic_cms.repository import InMemoryContentRepository, InMemoryContentTypeRepository


# ── ContentTypeRepository ────────────────────────────────────────────────────

def test_content_type_save_and_get() -> None:
    repo = InMemoryContentTypeRepository()
    schema = ContentTypeSchema(id="post", name="Post", fields=[])
    repo.save(schema)
    assert repo.get("post") == schema


def test_content_type_get_nonexistent_returns_none() -> None:
    repo = InMemoryContentTypeRepository()
    assert repo.get("ghost") is None


def test_content_type_exists() -> None:
    repo = InMemoryContentTypeRepository()
    schema = ContentTypeSchema(id="post", name="Post", fields=[])
    assert repo.exists("post") is False
    repo.save(schema)
    assert repo.exists("post") is True


def test_content_type_list_all() -> None:
    repo = InMemoryContentTypeRepository()
    repo.save(ContentTypeSchema(id="post", name="Post", fields=[]))
    repo.save(ContentTypeSchema(id="recipe", name="Recipe", fields=[]))
    result = repo.list_all()
    assert len(result) == 2
    ids = {s.id for s in result}
    assert ids == {"post", "recipe"}


def test_content_type_list_all_empty() -> None:
    repo = InMemoryContentTypeRepository()
    assert repo.list_all() == []


def test_content_type_delete_existing() -> None:
    repo = InMemoryContentTypeRepository()
    repo.save(ContentTypeSchema(id="post", name="Post", fields=[]))
    assert repo.delete("post") is True
    assert repo.get("post") is None


def test_content_type_delete_nonexistent() -> None:
    repo = InMemoryContentTypeRepository()
    assert repo.delete("ghost") is False


def test_content_type_save_overwrites() -> None:
    repo = InMemoryContentTypeRepository()
    repo.save(ContentTypeSchema(id="post", name="Old Name", fields=[]))
    repo.save(ContentTypeSchema(id="post", name="New Name", fields=[]))
    assert repo.get("post").name == "New Name"


# ── ContentRepository ────────────────────────────────────────────────────────

def test_content_save_and_get() -> None:
    repo = InMemoryContentRepository()
    entry = ContentEntry(id="abc", content_type_id="post", data={"title": "Hello"})
    repo.save(entry)
    assert repo.get("abc") == entry


def test_content_get_nonexistent_returns_none() -> None:
    repo = InMemoryContentRepository()
    assert repo.get("ghost") is None


def test_content_list_all_filtered_by_type() -> None:
    repo = InMemoryContentRepository()
    repo.save(ContentEntry(id="1", content_type_id="post", data={"title": "A"}))
    repo.save(ContentEntry(id="2", content_type_id="post", data={"title": "B"}))
    repo.save(ContentEntry(id="3", content_type_id="recipe", data={"title": "C"}))

    posts = repo.list_all("post")
    assert len(posts) == 2
    assert all(e.content_type_id == "post" for e in posts)

    recipes = repo.list_all("recipe")
    assert len(recipes) == 1


def test_content_list_all_empty() -> None:
    repo = InMemoryContentRepository()
    assert repo.list_all("post") == []


def test_content_delete_existing() -> None:
    repo = InMemoryContentRepository()
    entry = ContentEntry(id="abc", content_type_id="post", data={})
    repo.save(entry)
    assert repo.delete("abc") is True
    assert repo.get("abc") is None


def test_content_delete_nonexistent() -> None:
    repo = InMemoryContentRepository()
    assert repo.delete("ghost") is False


def test_content_save_overwrites() -> None:
    repo = InMemoryContentRepository()
    repo.save(ContentEntry(id="abc", content_type_id="post", data={"title": "Old"}))
    repo.save(ContentEntry(id="abc", content_type_id="post", data={"title": "New"}))
    assert repo.get("abc").data["title"] == "New"
