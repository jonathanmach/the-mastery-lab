"""
Experiment #3: Expands on the previous experiment by making the DB dependency request-bound

Results:
✅  Introduced new dependency: `logger`
[ ]  The `db_service` dependency is request-bound
    [ ] issues figuring out how to access the overridden dependency directly in the tests
--

Experiment #2: Services request-bound: Stop fighting the "get_dependency" approach and
create a `di` module where all dependencies are set-up

Results:
✅ di module with dependencies set-up works as expected
✅ override dependencies during tests (see tests/test_app.py)
"""

from fastapi import APIRouter, Depends, FastAPI

from . import di
from .services import ProductService


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(products_api)

    return app


# domains/products/api.py
products_api = APIRouter()


@products_api.get("/products")
# I want to explicitly leave `Depends()` empty instead of tight-coupling it to a implementation.
def list_products(product_service: ProductService = Depends(di.products_service)):
    #
    return product_service.get_products()


app = create_app()
