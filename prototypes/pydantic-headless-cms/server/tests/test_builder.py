from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from pydantic_cms.builder import build_model
from pydantic_cms.field_types import FieldDefinition, FieldType
from pydantic_cms.models import ContentTypeSchema


def make_schema(*fields: FieldDefinition) -> ContentTypeSchema:
    return ContentTypeSchema(id="test-type", name="Test", fields=list(fields))


def test_required_field_valid() -> None:
    schema = make_schema(FieldDefinition(name="title", type=FieldType.text, required=True))
    Model = build_model(schema)
    instance = Model(title="Hello")
    assert instance.title == "Hello"


def test_required_field_missing_raises() -> None:
    schema = make_schema(FieldDefinition(name="title", type=FieldType.text, required=True))
    Model = build_model(schema)
    with pytest.raises(ValidationError):
        Model()


def test_optional_field_defaults_to_none() -> None:
    schema = make_schema(FieldDefinition(name="subtitle", type=FieldType.text, required=False))
    Model = build_model(schema)
    instance = Model()
    assert instance.subtitle is None


def test_optional_field_accepts_value() -> None:
    schema = make_schema(FieldDefinition(name="subtitle", type=FieldType.text, required=False))
    Model = build_model(schema)
    instance = Model(subtitle="Sub")
    assert instance.subtitle == "Sub"


def test_integer_field_rejects_non_coercible_string() -> None:
    schema = make_schema(FieldDefinition(name="count", type=FieldType.integer, required=True))
    Model = build_model(schema)
    with pytest.raises(ValidationError):
        Model(count="not-a-number")


def test_integer_field_accepts_int() -> None:
    schema = make_schema(FieldDefinition(name="count", type=FieldType.integer, required=True))
    Model = build_model(schema)
    instance = Model(count=42)
    assert instance.count == 42


def test_boolean_field() -> None:
    schema = make_schema(FieldDefinition(name="published", type=FieldType.boolean, required=True))
    Model = build_model(schema)
    assert Model(published=True).published is True
    assert Model(published=False).published is False


def test_list_field_accepts_list() -> None:
    schema = make_schema(
        FieldDefinition(name="tags", type=FieldType.list_, required=True, item_type=FieldType.text)
    )
    Model = build_model(schema)
    instance = Model(tags=["python", "pydantic"])
    assert instance.tags == ["python", "pydantic"]


def test_list_field_rejects_wrong_item_type() -> None:
    schema = make_schema(
        FieldDefinition(name="scores", type=FieldType.list_, required=True, item_type=FieldType.integer)
    )
    Model = build_model(schema)
    with pytest.raises(ValidationError):
        Model(scores=["not", "numbers"])


def test_multiple_fields() -> None:
    schema = make_schema(
        FieldDefinition(name="title", type=FieldType.text, required=True),
        FieldDefinition(name="body", type=FieldType.rich_text, required=True),
        FieldDefinition(name="views", type=FieldType.integer, required=False),
    )
    Model = build_model(schema)
    instance = Model(title="Hi", body="<p>Hello</p>")
    assert instance.title == "Hi"
    assert instance.views is None


def test_model_name_matches_schema_id() -> None:
    schema = make_schema(FieldDefinition(name="title", type=FieldType.text))
    Model = build_model(schema)
    assert Model.__name__ == "TestType"
