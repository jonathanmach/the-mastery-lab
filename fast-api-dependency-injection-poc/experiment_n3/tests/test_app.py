from fastapi.testclient import TestClient
from pytest import fixture

from .. import di
from ..main import app
from ..services import DatabaseService

# I couldn't figure out how to access the overridden dependency directly in the tests,
# so I'm using a global variable to test that the dependency is request-bound.
_request_counter = 0


class TestDBService(DatabaseService):
    # TODO: Should test fakes live near the real implementation? Or inside the tests folder?
    def __init__(self):
        """
        To test that this is request-bound, we can examine whether the dependency
        creates a new instance or maintains state across multiple requests.
        """
        global _request_counter
        _request_counter = 0

    def get_objects(self):
        global _request_counter
        _request_counter += 1

        return [
            {"name": "Product Test1", "quantity": 10},
            {"name": "Product Test2", "quantity": 20},
        ]


@fixture
def db_service():
    return TestDBService


@fixture
def test_app(db_service):
    app.dependency_overrides[di.db_service] = db_service
    return TestClient(app)


def test_db_is_request_bound(test_app: TestClient):
    # First request
    response = test_app.get("/products")
    assert response.status_code == 200

    # Second request
    response = test_app.get("/products")
    assert response.status_code == 200

    # Access the overridden dependency directly
    assert _request_counter == 1


def test_list_products(test_app):
    response = test_app.get("/products")
    assert response.status_code == 200
    assert response.json() == [
        {"name": "Product Test1", "quantity": 10},
        {"name": "Product Test2", "quantity": 20},
    ]
