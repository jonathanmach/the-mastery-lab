from fastapi.testclient import TestClient
from pytest import fixture

from .. import di
from ..main import app
from ..services import DatabaseService


# TODO: Should test fakes live near the real implementation? Or inside the tests folder?
class TestDBService(DatabaseService):
    def __init__(self):
        """
        To test if something is request-bound in FastAPI, you can examine whether a
        dependency creates a new instance or maintains state across multiple requests.
        """
        self.request_counter = 0

    def get_objects(self):
        self.request_counter += 1

        return [
            {"name": "Product Test1", "quantity": 10},
            {"name": "Product Test2", "quantity": 20},
        ]


def db_service():
    return TestDBService()


@fixture
def test_app():
    # Override dependencies
    app.dependency_overrides[di.db_service] = db_service
    return TestClient(app)


def test_request_bound(test_app):
    # First request
    response = test_app.get("/products")
    assert response.status_code == 200

    # Second request
    response = test_app.get("/products")
    assert response.status_code == 200

    # Access the overridden dependency directly
    db_service_instance = ????

    # Check if the request counter resets,  counter should be reset per request
    assert db_service_instance.request_counter == 1


def test_list_products(test_app):
    response = test_app.get("/products")
    assert response.status_code == 200
    assert response.json() == [
        {"name": "Product Test1", "quantity": 10},
        {"name": "Product Test2", "quantity": 20},
    ]
