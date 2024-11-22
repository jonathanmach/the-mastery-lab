from fastapi.testclient import TestClient
from pytest import fixture

from .. import di
from ..main import app
from ..services import DatabaseService


@fixture
def db_service():
    class TestDBService(DatabaseService):
        # TODO: Should test fakes live near the real implementation? Or inside the tests folder?
        def get_objects(self):
            return [
                {"name": "Product Test1", "quantity": 10},
                {"name": "Product Test2", "quantity": 20},
            ]

    return TestDBService


@fixture
def test_app(db_service):
    # Override dependencies
    app.dependency_overrides[di.db_service] = db_service
    return TestClient(app)


def test_list_products(test_app):
    response = test_app.get("/products")
    assert response.status_code == 200
    assert response.json() == [
        {"name": "Product Test1", "quantity": 10},
        {"name": "Product Test2", "quantity": 20},
    ]
