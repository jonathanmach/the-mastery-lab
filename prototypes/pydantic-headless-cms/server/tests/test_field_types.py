from __future__ import annotations

import datetime

import pytest
from pydantic import ValidationError

from pydantic_cms.field_types import FieldDefinition, FieldType


def test_scalar_field_defaults() -> None:
    field = FieldDefinition(name="title", type=FieldType.text)
    assert field.required is True
    assert field.item_type is None


def test_required_false() -> None:
    field = FieldDefinition(name="subtitle", type=FieldType.text, required=False)
    assert field.required is False


def test_list_field_requires_item_type() -> None:
    with pytest.raises(ValidationError):
        FieldDefinition(name="tags", type=FieldType.list_)


def test_list_field_with_item_type() -> None:
    field = FieldDefinition(name="tags", type=FieldType.list_, item_type=FieldType.text)
    assert field.item_type == FieldType.text


def test_list_field_rejects_nested_list() -> None:
    with pytest.raises(ValidationError):
        FieldDefinition(name="nested", type=FieldType.list_, item_type=FieldType.list_)


def test_non_list_field_rejects_item_type() -> None:
    with pytest.raises(ValidationError):
        FieldDefinition(name="title", type=FieldType.text, item_type=FieldType.text)


def test_to_annotation_text() -> None:
    assert FieldDefinition(name="f", type=FieldType.text).to_annotation() is str


def test_to_annotation_rich_text() -> None:
    assert FieldDefinition(name="f", type=FieldType.rich_text).to_annotation() is str


def test_to_annotation_number() -> None:
    assert FieldDefinition(name="f", type=FieldType.number).to_annotation() is float


def test_to_annotation_integer() -> None:
    assert FieldDefinition(name="f", type=FieldType.integer).to_annotation() is int


def test_to_annotation_boolean() -> None:
    assert FieldDefinition(name="f", type=FieldType.boolean).to_annotation() is bool


def test_to_annotation_date() -> None:
    assert FieldDefinition(name="f", type=FieldType.date).to_annotation() is datetime.date


def test_to_annotation_datetime() -> None:
    assert (
        FieldDefinition(name="f", type=FieldType.datetime_).to_annotation()
        is datetime.datetime
    )


def test_to_annotation_list_of_text() -> None:
    field = FieldDefinition(name="tags", type=FieldType.list_, item_type=FieldType.text)
    assert field.to_annotation() == list[str]


def test_to_annotation_list_of_integer() -> None:
    field = FieldDefinition(name="scores", type=FieldType.list_, item_type=FieldType.integer)
    assert field.to_annotation() == list[int]
