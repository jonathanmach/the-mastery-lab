from __future__ import annotations

from pydantic_cms.models import ContentEntry, ContentTypeSchema
from pydantic_cms.repository import ContentRepository, ContentTypeRepository


# ── ContentTypeRepository ────────────────────────────────────────────────────

def test_content_type_save_and_get(content_type_repo: ContentTypeRepository) -> None:
    schema = ContentTypeSchema(id="post", name="Post", fields=[])
    content_type_repo.save(schema)
    assert content_type_repo.get("post") == schema


def test_content_type_get_nonexistent_returns_none(content_type_repo: ContentTypeRepository) -> None:
    assert content_type_repo.get("ghost") is None


def test_content_type_exists(content_type_repo: ContentTypeRepository) -> None:
    schema = ContentTypeSchema(id="post", name="Post", fields=[])
    assert content_type_repo.exists("post") is False
    content_type_repo.save(schema)
    assert content_type_repo.exists("post") is True


def test_content_type_list_all(content_type_repo: ContentTypeRepository) -> None:
    content_type_repo.save(ContentTypeSchema(id="post", name="Post", fields=[]))
    content_type_repo.save(ContentTypeSchema(id="recipe", name="Recipe", fields=[]))
    result = content_type_repo.list_all()
    assert len(result) == 2
    ids = {s.id for s in result}
    assert ids == {"post", "recipe"}


def test_content_type_list_all_empty(content_type_repo: ContentTypeRepository) -> None:
    assert content_type_repo.list_all() == []


def test_content_type_delete_existing(content_type_repo: ContentTypeRepository) -> None:
    content_type_repo.save(ContentTypeSchema(id="post", name="Post", fields=[]))
    assert content_type_repo.delete("post") is True
    assert content_type_repo.get("post") is None


def test_content_type_delete_nonexistent(content_type_repo: ContentTypeRepository) -> None:
    assert content_type_repo.delete("ghost") is False


def test_content_type_save_overwrites(content_type_repo: ContentTypeRepository) -> None:
    content_type_repo.save(ContentTypeSchema(id="post", name="Old Name", fields=[]))
    content_type_repo.save(ContentTypeSchema(id="post", name="New Name", fields=[]))
    result = content_type_repo.get("post")
    assert result is not None
    assert result.name == "New Name"


# ── ContentRepository ────────────────────────────────────────────────────────

def test_content_save_and_get(content_repo: ContentRepository) -> None:
    entry = ContentEntry(id="abc", content_type_id="post", data={"title": "Hello"})
    content_repo.save(entry)
    assert content_repo.get("abc") == entry


def test_content_get_nonexistent_returns_none(content_repo: ContentRepository) -> None:
    assert content_repo.get("ghost") is None


def test_content_list_all_filtered_by_type(content_repo: ContentRepository) -> None:
    content_repo.save(ContentEntry(id="1", content_type_id="post", data={"title": "A"}))
    content_repo.save(ContentEntry(id="2", content_type_id="post", data={"title": "B"}))
    content_repo.save(ContentEntry(id="3", content_type_id="recipe", data={"title": "C"}))

    posts = content_repo.list_all("post")
    assert len(posts) == 2
    assert all(e.content_type_id == "post" for e in posts)

    recipes = content_repo.list_all("recipe")
    assert len(recipes) == 1


def test_content_list_all_empty(content_repo: ContentRepository) -> None:
    assert content_repo.list_all("post") == []


def test_content_delete_existing(content_repo: ContentRepository) -> None:
    entry = ContentEntry(id="abc", content_type_id="post", data={})
    content_repo.save(entry)
    assert content_repo.delete("abc") is True
    assert content_repo.get("abc") is None


def test_content_delete_nonexistent(content_repo: ContentRepository) -> None:
    assert content_repo.delete("ghost") is False


def test_content_save_overwrites(content_repo: ContentRepository) -> None:
    content_repo.save(ContentEntry(id="abc", content_type_id="post", data={"title": "Old"}))
    content_repo.save(ContentEntry(id="abc", content_type_id="post", data={"title": "New"}))
    result = content_repo.get("abc")
    assert result is not None
    assert result.data["title"] == "New"
