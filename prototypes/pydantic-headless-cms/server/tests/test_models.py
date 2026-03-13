from __future__ import annotations

import pytest
from pydantic import ValidationError

from pydantic_cms.field_types import FieldDefinition, FieldType
from pydantic_cms.models import ContentTypeSchema


def test_valid_slug_id() -> None:
    schema = ContentTypeSchema(id="blog-post", name="Blog Post", fields=[])
    assert schema.id == "blog-post"


def test_single_word_id() -> None:
    schema = ContentTypeSchema(id="recipe", name="Recipe", fields=[])
    assert schema.id == "recipe"


def test_invalid_id_uppercase() -> None:
    with pytest.raises(ValidationError):
        ContentTypeSchema(id="BlogPost", name="Blog Post", fields=[])


def test_invalid_id_spaces() -> None:
    with pytest.raises(ValidationError):
        ContentTypeSchema(id="blog post", name="Blog Post", fields=[])


def test_invalid_id_leading_hyphen() -> None:
    with pytest.raises(ValidationError):
        ContentTypeSchema(id="-blog-post", name="Blog Post", fields=[])


def test_json_round_trip(blog_post_schema: ContentTypeSchema) -> None:
    json_str = blog_post_schema.model_dump_json()
    restored = ContentTypeSchema.model_validate_json(json_str)
    assert restored == blog_post_schema


def test_fields_preserved_in_round_trip(blog_post_schema: ContentTypeSchema) -> None:
    json_str = blog_post_schema.model_dump_json()
    restored = ContentTypeSchema.model_validate_json(json_str)
    assert len(restored.fields) == len(blog_post_schema.fields)
    tags_field = next(f for f in restored.fields if f.name == "tags")
    assert tags_field.item_type == FieldType.text
