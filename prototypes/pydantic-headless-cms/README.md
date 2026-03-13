# pydantic-headless-cms

A framework-agnostic headless CMS prototype powered by Pydantic. Administrators define **content types** composed of typed fields; content submitted against those types is validated at runtime by dynamically-generated Pydantic models.

## Concepts

### Content Types

A content type is a named schema (e.g. "Blog Post", "Recipe") made up of fields. Each field has a name, a type, and an optional/required flag.

Supported field types:

| Type | Python type |
|------|-------------|
| `text` | `str` |
| `rich_text` | `str` (HTML or Markdown) |
| `number` | `float` |
| `integer` | `int` |
| `boolean` | `bool` |
| `date` | `datetime.date` |
| `datetime` | `datetime.datetime` |
| `list` | `list[<item_type>]` |

`list` fields require an `item_type` drawn from the scalar types above. Nested lists are not supported.

Content type IDs are lowercase slugs (e.g. `blog-post`, `recipe`).

### Content Entries

Once a content type is defined, content can be created against it. On every write (create or update) the submitted data is validated by a Pydantic model built from the schema. Invalid data raises `pydantic.ValidationError`.

### Repository Pattern

Storage is abstracted behind two repository interfaces:

- `ContentTypeRepository` — CRUD for content type schemas
- `ContentRepository` — CRUD for content entries

The package ships `InMemoryContentTypeRepository` and `InMemoryContentRepository` for testing and local development. Swap in a database-backed implementation without touching any other code.

## Usage

```python
from pydantic_cms import (
    CMS,
    ContentTypeSchema,
    FieldDefinition,
    FieldType,
    InMemoryContentRepository,
    InMemoryContentTypeRepository,
)

cms = CMS(
    content_type_repo=InMemoryContentTypeRepository(),
    content_repo=InMemoryContentRepository(),
)

# Define a content type
cms.define_content_type(
    ContentTypeSchema(
        id="recipe",
        name="Recipe",
        fields=[
            FieldDefinition(name="title",       type=FieldType.text,    required=True),
            FieldDefinition(name="servings",     type=FieldType.integer, required=True),
            FieldDefinition(name="ingredients",  type=FieldType.list_,   required=True,
                            item_type=FieldType.text),
            FieldDefinition(name="notes",        type=FieldType.rich_text, required=False),
        ],
    )
)

# Create a content entry (validated against the schema)
entry = cms.create_content("recipe", {
    "title": "Pasta Carbonara",
    "servings": 2,
    "ingredients": ["spaghetti", "eggs", "pancetta", "pecorino"],
})

print(entry.id)               # uuid4 string
print(entry.data["title"])    # "Pasta Carbonara"

# Read, update, delete
entry = cms.get_content(entry.id)
entry = cms.update_content(entry.id, {**entry.data, "servings": 4})
cms.delete_content(entry.id)
```

Validation errors surface directly from Pydantic:

```python
from pydantic import ValidationError

try:
    cms.create_content("recipe", {"servings": 2})  # missing required 'title'
except ValidationError as e:
    print(e)
```

## Project Structure

```
pydantic_cms/
├── field_types.py   # FieldType enum + FieldDefinition model
├── models.py        # ContentTypeSchema, ContentEntry
├── builder.py       # build_model() — creates Pydantic models at runtime
├── repository.py    # Repository ABCs + InMemory implementations
└── cms.py           # CMS facade (public API)

tests/
├── conftest.py
├── test_field_types.py
├── test_models.py
├── test_builder.py
├── test_repository.py
└── test_cms.py
```

## Development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
uv run pytest tests/ -v
```

## Design Notes

- **No web framework dependency.** The `CMS` class is plain Python. Wrap it with FastAPI, Django, or anything else.
- **Dynamic model generation.** `build_model()` calls `pydantic.create_model()` on each content write. A caching layer (registry) can be added later without changing the public API.
- **Swappable storage.** Implement `ContentTypeRepository` and `ContentRepository` to back the CMS with any database.
