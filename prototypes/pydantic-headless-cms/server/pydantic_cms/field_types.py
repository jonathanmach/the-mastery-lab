from __future__ import annotations

import datetime
from enum import Enum
from typing import Any

import pydantic


class FieldType(str, Enum):
    text = "text"
    rich_text = "rich_text"
    number = "number"
    integer = "integer"
    boolean = "boolean"
    date = "date"
    datetime_ = "datetime"
    list_ = "list"


SCALAR_TYPE_MAP: dict[FieldType, type] = {
    FieldType.text: str,
    FieldType.rich_text: str,
    FieldType.number: float,
    FieldType.integer: int,
    FieldType.boolean: bool,
    FieldType.date: datetime.date,
    FieldType.datetime_: datetime.datetime,
}


class FieldDefinition(pydantic.BaseModel):
    name: str
    type: FieldType
    required: bool = True
    item_type: FieldType | None = None

    @pydantic.model_validator(mode="after")
    def _validate_list_item_type(self) -> FieldDefinition:
        if self.type == FieldType.list_:
            if self.item_type is None:
                raise ValueError("Fields of type 'list' must specify item_type")
            if self.item_type == FieldType.list_:
                raise ValueError("Nested lists are not supported")
        else:
            if self.item_type is not None:
                raise ValueError("item_type is only valid for list fields")
        return self

    def to_annotation(self) -> Any:
        if self.type == FieldType.list_:
            return list[SCALAR_TYPE_MAP[self.item_type]]
        return SCALAR_TYPE_MAP[self.type]
