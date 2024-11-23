import pytest
from fast_depends import dependency_provider, inject, Depends

from app import WebhookService
from app_3_fastdepends import create_app, get_webhook_service


class FakeWebhookService(WebhookService):
    def process_webhook(self, payload):
        print("Fake processing webhook:", payload)


def get_fake_webhook_service():
    return FakeWebhookService()


@pytest.fixture
def test_app():
    flask_app = create_app()

    # Override the dependency
    dependency_provider.override(get_webhook_service, get_fake_webhook_service)
    # or
    # dependency_provider.dependency_overrides[original_dependency] = override_dependency

    with flask_app.test_client() as test_client:
        yield test_client


def test_dependency_overriding(test_app):
    res = test_app.get("/exp1")
    assert res.status_code == 200, res.data


def test_dependency_overriding_exp2(test_app):
    # Exp2: Uses Annotated
    res = test_app.post("/exp2", json={"payload": {"foo": "bar"}})
    assert res.status_code == 200, res.data
