from fastapi import APIRouter, Depends, FastAPI


class DatabaseService:
    def __init__(self):
        pass


class ProductService:
    def __init__(self, db: DatabaseService):
        self.db = db
        ...

    def get_products(self) -> list[dict]:
        # Get products from database
        # db...
        return [
            {"name": "Product 1", "quantity": 10},
            {"name": "Product 2", "quantity": 20},
        ]


def create_app() -> FastAPI:
    app = FastAPI()

    # Dependency setup
    db_service = DatabaseService()
    product_service = ProductService(db=db_service)
    # ...
    # many more services...

    # Bind all dependencies
    app.dependency_overrides[ProductService] = lambda: product_service

    app.include_router(products_api)

    return app


products_api = APIRouter()


@products_api.get("/products")
# Trying to explicitly leave `Depends()` empty instead of having to tight-couple it to a implementation.
def list_products(product_service: ProductService = Depends()):
    #
    return product_service.get_products()


app = create_app()

"""
FastAPIError: Invalid args for response field! Hint: check that <class 'app_issue1.DatabaseService'> is a valid Pydantic field type. If you are using a return 
type annotation that is not a valid Pydantic field (e.g. Union[Response, dict, None]) you can disable generating the response model from the type annotation with
the path operation decorator parameter response_model=None. Read more: https://fastapi.tiangolo.com/tutorial/response-model/

│ /Users/jonathan/Library/Caches/pypoetry/virtualenvs/fast-api-dependency-injection-poc-IXtrcyBV-py3.12/lib/python3.12/site-packages/fastapi/utils.py:98 in     │
│ create_model_field                                                                                                                                            │
│                                                                                                                                                               │
│    95 │   try:                                                                                                                                                │
│    96 │   │   return ModelField(**kwargs)  # type: ignore[arg-type]                                                                                           │
│    97 │   except (RuntimeError, PydanticSchemaGenerationError):                                                                                               │
│ ❱  98 │   │   raise fastapi.exceptions.FastAPIError(                                                                                                          │
│    99 │   │   │   "Invalid args for response field! Hint: "                                                                                                   │
│   100 │   │   │   f"check that {type_} is a valid Pydantic field type. "                                                                                      │
│   101 │   │   │   "If you are using a return type annotation that is not a valid Pydantic "                                                                   │
│                                                                                                                                                               │
│ ╭───────────────────────────────────────────────────────────────────────── locals ──────────────────────────────────────────────────────────────────────────╮ │
│ │            alias = 'db'                                                                                                                                   │ │
│ │ class_validators = {}                                                                                                                                     │ │
│ │          default = PydanticUndefined                                                                                                                      │ │
│ │       field_info = Query(annotation=DatabaseService, required=True, alias='db', json_schema_extra={})                                                     │ │
│ │           kwargs = {'name': 'db', 'field_info': Query(annotation=DatabaseService, required=True, alias='db', json_schema_extra={}), 'mode': 'validation'} │ │
│ │             mode = 'validation'                                                                                                                           │ │
│ │             name = 'db'                                                                                                                                   │ │
│ │         required = True                                                                                                                                   │ │
│ ╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯ │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
"""
