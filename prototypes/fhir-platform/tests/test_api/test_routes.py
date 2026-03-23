from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.dependencies import get_fhir_client, get_search_projector


@pytest.fixture
def mock_projector():
    proj = MagicMock()
    proj.search.return_value = {"total": 1, "page": 1, "page_size": 20, "results": [
        {
            "patient_id": "patient-001",
            "name": "John Smith",
            "family_name": "Smith",
            "given_name": "John",
            "gender": "male",
            "birth_date": "1980-06-15",
            "age_band": "35-49",
            "conditions": ["Diabetes mellitus type 2"],
            "condition_codes": ["44054006"],
            "medications": ["Metformin 500 MG"],
            "medication_codes": ["860975"],
            "last_encounter_date": "2024-01-10",
            "has_active_medication": True,
            "has_recent_encounter": False,
            "validation_status": "usable",
        }
    ]}
    proj.facets.return_value = {
        "gender": [{"key": "male", "count": 1}],
        "age_band": [{"key": "35-49", "count": 1}],
        "diagnosis": [{"key": "44054006", "count": 1}],
        "medication": [{"key": "860975", "count": 1}],
        "recent_encounter": [{"key": "false", "count": 1}],
    }
    return proj


@pytest.fixture
def mock_fhir():
    client = MagicMock()
    client.get_resource.return_value = {
        "resourceType": "Patient",
        "id": "patient-001",
        "name": [{"family": "Smith", "given": ["John"]}],
        "gender": "male",
        "birthDate": "1980-06-15",
        "address": [{"line": ["123 Main St"], "city": "Springfield", "state": "MA", "postalCode": "01101"}],
    }
    client.get_patient_resources.return_value = []
    return client


@pytest.fixture
def api_client(mock_projector, mock_fhir):
    app.dependency_overrides[get_search_projector] = lambda: mock_projector
    app.dependency_overrides[get_fhir_client] = lambda: mock_fhir
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_search_patients(api_client, mock_projector):
    resp = api_client.get("/patients/search?q=Smith&gender=male")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["results"][0]["name"] == "John Smith"
    mock_projector.search.assert_called_once()


def test_facets(api_client, mock_projector):
    resp = api_client.get("/patients/facets")
    assert resp.status_code == 200
    data = resp.json()
    assert "gender" in data
    assert data["gender"][0]["key"] == "male"


def test_patient_summary(api_client, mock_fhir):
    resp = api_client.get("/patients/patient-001/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient_id"] == "patient-001"
    assert data["name"] == "John Smith"
    assert data["gender"] == "male"


def test_patient_timeline(api_client):
    resp = api_client.get("/patients/patient-001/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient_id"] == "patient-001"
    assert isinstance(data["events"], list)


def test_patient_resources(api_client):
    resp = api_client.get("/patients/patient-001/resources?type=Observation")
    assert resp.status_code == 200
