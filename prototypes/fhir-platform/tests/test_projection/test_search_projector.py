import pytest

from app.projection.search_projector import SearchProjector, _age_band, _validation_status


# ------------------------------------------------------------------
# Unit tests for pure helper functions (no I/O)
# ------------------------------------------------------------------


def test_age_band_child():
    assert _age_band("2015-01-01") == "<18"


def test_age_band_young_adult():
    assert _age_band("1995-01-01") == "18-34"


def test_age_band_senior():
    assert _age_band("1955-01-01") == "65+"


def test_age_band_none():
    assert _age_band(None) is None


def test_validation_status_usable():
    assert _validation_status(True, True, True, False) == "usable"


def test_validation_status_partial():
    assert _validation_status(True, True, False, False) == "partial"


def test_validation_status_insufficient_no_encounter():
    assert _validation_status(True, False, True, True) == "insufficient"


def test_validation_status_insufficient_no_patient():
    assert _validation_status(False, True, True, True) == "insufficient"


# ------------------------------------------------------------------
# SearchProjector._build_doc (no external I/O)
# ------------------------------------------------------------------


@pytest.fixture
def projector_no_os(monkeypatch):
    """SearchProjector with OpenSearch client stubbed out — no Docker required."""
    from unittest.mock import MagicMock

    mock_os = MagicMock()
    mock_os.indices.exists.return_value = True
    proj = SearchProjector.__new__(SearchProjector)
    proj._client = mock_os
    proj._index = "patients"
    return proj


def test_build_doc_basic(projector_no_os):
    patient = {
        "id": "p-1",
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "gender": "female",
        "birthDate": "1990-03-20",
    }
    encounters = [{"id": "e-1", "period": {"start": "2024-06-01"}}]
    conditions = [
        {
            "id": "c-1",
            "code": {
                "coding": [{"system": "http://snomed.info/sct", "code": "44054006", "display": "Diabetes mellitus type 2"}]
            },
            "recordedDate": "2024-01-01",
        }
    ]
    observations = []
    medications = [
        {
            "id": "m-1",
            "status": "active",
            "medicationCodeableConcept": {
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "860975", "display": "Metformin 500 MG"}]
            },
            "authoredOn": "2024-01-01",
        }
    ]

    doc = projector_no_os._build_doc(patient, encounters, conditions, observations, medications)

    assert doc["patient_id"] == "p-1"
    assert doc["family_name"] == "Doe"
    assert doc["given_name"] == "Jane"
    assert doc["gender"] == "female"
    assert "44054006" in doc["condition_codes"]
    assert "860975" in doc["medication_codes"]
    assert doc["has_active_medication"] is True
    assert doc["validation_status"] == "usable"
