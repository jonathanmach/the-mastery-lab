import pytest

from app import create_app, create_flask_openapi3_app


@pytest.fixture
def test_app():
    flask_app = create_app()
    # with flask_app.app_context():
    with flask_app.test_client() as test_client:
        yield test_client

@pytest.fixture
def test_app_openapi3():
    flask_app = create_flask_openapi3_app()
    # with flask_app.app_context():
    with flask_app.test_client() as test_client:
        yield test_client

@pytest.fixture
def test_app():
    flask_app = create_app()
    # with flask_app.app_context():
    with flask_app.test_client() as test_client:
        yield test_client

def test_hello_word(test_app):
    res = test_app.get('/')
    assert res.status_code == 200

def test_flask_injector_selective_injection(test_app):
    res = test_app.post('/my-webhook', json={"payload": {"foo": "bar"}})
    assert res.status_code == 200

def test_flask_pydantic(test_app):
    res = test_app.post('/my-webhook2', json={"payload": {"foo": "bar"}})
    assert res.status_code == 200, res.data


def test_flask_openapi3(test_app_openapi3):
    res = test_app_openapi3.post('/flask-openapi3', json={"payload": {"foo": "bar"}})
    assert res.status_code == 200, res.data