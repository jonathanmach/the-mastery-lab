import pytest

from app.ingestion.bundle_parser import SUPPORTED_RESOURCE_TYPES, parse_bundle


def test_parse_returns_five_supported_resources(sample_bundle):
    result = parse_bundle(sample_bundle)
    assert result.bundle_id == "test-bundle-001"
    # Practitioner is skipped; 5 supported resources remain
    assert len(result.resources) == 5


def test_resource_types_are_supported(sample_bundle):
    result = parse_bundle(sample_bundle)
    for res in result.resources:
        assert res.resource_type in SUPPORTED_RESOURCE_TYPES


def test_patient_has_correct_id(sample_bundle):
    result = parse_bundle(sample_bundle)
    patient = next(r for r in result.resources if r.resource_type == "Patient")
    assert patient.logical_id == "patient-001"
    assert patient.error is None


def test_no_errors_on_valid_bundle(sample_bundle):
    result = parse_bundle(sample_bundle)
    errors = [r for r in result.resources if r.error is not None]
    assert errors == [], f"Unexpected errors: {[(r.resource_type, r.error) for r in errors]}"


def test_invalid_bundle_raises():
    with pytest.raises(ValueError, match="Invalid FHIR Bundle"):
        parse_bundle({"resourceType": "NotABundle"})


def test_resource_without_id_is_skipped(sample_bundle):
    # Append a resource with no id — it should be silently skipped
    sample_bundle["entry"].append(
        {"resource": {"resourceType": "Patient"}}  # no id
    )
    result = parse_bundle(sample_bundle)
    # still only 5 supported resources (the id-less Patient was skipped)
    assert len(result.resources) == 5
