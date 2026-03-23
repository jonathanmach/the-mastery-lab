import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db.session import get_session

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sqlite_db(tmp_path):
    """In-memory SQLite DB with all tables created."""
    db_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return db_url


@pytest.fixture
def db_session(sqlite_db):
    engine = create_engine(sqlite_db, connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine)
    session = factory()
    yield session
    session.close()


@pytest.fixture
def sample_bundle() -> dict:
    """Minimal synthetic Synthea-style FHIR bundle with one patient."""
    return {
        "resourceType": "Bundle",
        "id": "test-bundle-001",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-001",
                    "name": [{"family": "Smith", "given": ["John"]}],
                    "gender": "male",
                    "birthDate": "1980-06-15",
                }
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "encounter-001",
                    "status": "finished",
                    "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
                    "subject": {"reference": "Patient/patient-001"},
                    "period": {"start": "2024-01-10", "end": "2024-01-10"},
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "condition-001",
                    "clinicalStatus": {
                        "coding": [
                            {"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}
                        ]
                    },
                    "subject": {"reference": "Patient/patient-001"},
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "44054006",
                                "display": "Diabetes mellitus type 2",
                            }
                        ]
                    },
                    "recordedDate": "2024-01-10",
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-001",
                    "status": "final",
                    "subject": {"reference": "Patient/patient-001"},
                    "code": {
                        "coding": [
                            {"system": "http://loinc.org", "code": "2339-0", "display": "Glucose [Mass/volume] in Blood"}
                        ]
                    },
                    "effectiveDateTime": "2024-01-10",
                    "valueQuantity": {"value": 140, "unit": "mg/dL"},
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "med-001",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/patient-001"},
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "860975",
                                "display": "Metformin 500 MG",
                            }
                        ]
                    },
                    "authoredOn": "2024-01-10",
                }
            },
            {
                # should be silently skipped (unsupported type)
                "resource": {
                    "resourceType": "Practitioner",
                    "id": "prac-001",
                    "name": [{"family": "Jones"}],
                }
            },
        ],
    }
