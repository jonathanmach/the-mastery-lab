import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import (
    PatientFacetsResponse,
    PatientSearchResponse,
    PatientSummary,
    PatientTimeline,
    TimelineEvent,
)
from app.dependencies import FHIRClientDep, SearchProjectorDep
from app.projection.search_projector import _age_band, _extract_display, _resource_date

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search", response_model=PatientSearchResponse)
def search_patients(
    projector: SearchProjectorDep,
    q: str = Query(default=""),
    gender: str | None = Query(default=None),
    condition: str | None = Query(default=None),
    medication: str | None = Query(default=None),
    age_band: str | None = Query(default=None),
    recent_encounter: bool | None = Query(default=None),
    observation: str | None = Query(default=None),
    obs_min: float | None = Query(default=None),
    obs_max: float | None = Query(default=None),
    page: int = Query(default=1, ge=1),
):
    return projector.search(
        q=q,
        gender=gender,
        condition=condition,
        medication=medication,
        age_band=age_band,
        recent_encounter=recent_encounter,
        observation=observation,
        obs_min=obs_min,
        obs_max=obs_max,
        page=page,
    )


@router.get("/facets", response_model=PatientFacetsResponse)
def get_facets(
    projector: SearchProjectorDep,
    gender: str | None = Query(default=None),
    condition: str | None = Query(default=None),
    medication: str | None = Query(default=None),
    age_band: str | None = Query(default=None),
    observation: str | None = Query(default=None),
):
    return projector.facets(
        gender=gender, condition=condition, medication=medication,
        age_band=age_band, observation=observation,
    )


@router.get("/{patient_id}/summary", response_model=PatientSummary)
def get_patient_summary(patient_id: str, fhir_client: FHIRClientDep):
    try:
        patient = fhir_client.get_resource("Patient", patient_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found") from exc

    conditions = fhir_client.get_patient_resources(patient_id, "Condition")
    medications = fhir_client.get_patient_resources(patient_id, "MedicationRequest")
    observations = fhir_client.get_patient_resources(patient_id, "Observation")
    encounters = fhir_client.get_patient_resources(patient_id, "Encounter")

    names = patient.get("name") or []
    family = names[0].get("family") if names else None
    given_list = names[0].get("given") or [] if names else []
    given = given_list[0] if given_list else None
    full_name = " ".join(filter(None, [given, family])) or patient_id

    addr = (patient.get("address") or [{}])[0]
    address_parts = filter(
        None,
        [
            ", ".join(addr.get("line") or []),
            addr.get("city"),
            addr.get("state"),
            addr.get("postalCode"),
        ],
    )
    address_str = ", ".join(address_parts) or None

    birth_date = patient.get("birthDate")

    # Latest observations keyed by LOINC code
    latest_obs: dict[str, dict] = {}
    for obs in sorted(observations, key=lambda o: _resource_date(o) or "", reverse=True):
        for coding in obs.get("code", {}).get("coding") or []:
            code = coding.get("code")
            if code and code not in latest_obs:
                value = obs.get("valueQuantity") or obs.get("valueString") or obs.get("valueCodeableConcept")
                category_codings = (obs.get("category") or [{}])[0].get("coding") or [{}]
                interp_codings = (obs.get("interpretation") or [{}])[0].get("coding") or [{}]
                latest_obs[code] = {
                    "id": obs.get("id"),
                    "code": code,
                    "display": coding.get("display", code),
                    "value": value,
                    "date": _resource_date(obs),
                    "status": obs.get("status"),
                    "category": category_codings[0].get("display") or category_codings[0].get("code"),
                    "interpretation": interp_codings[0].get("code"),
                    "referenceRange": obs.get("referenceRange"),
                    "components": obs.get("component"),
                    "note": [n.get("text") for n in (obs.get("note") or []) if n.get("text")],
                }

    from app.projection.search_projector import _validation_status

    validation = _validation_status(
        has_patient=True,
        has_encounter=bool(encounters),
        has_condition=bool(conditions),
        has_observation=bool(observations),
    )

    return PatientSummary(
        patient_id=patient_id,
        name=full_name,
        gender=patient.get("gender"),
        birth_date=birth_date,
        age_band=_age_band(birth_date),
        address=address_str,
        conditions=conditions,
        medications=medications,
        latest_observations=list(latest_obs.values()),
        encounters=encounters,
        validation_status=validation,
    )


@router.get("/{patient_id}/timeline", response_model=PatientTimeline)
def get_patient_timeline(patient_id: str, fhir_client: FHIRClientDep):
    encounters = fhir_client.get_patient_resources(patient_id, "Encounter")
    conditions = fhir_client.get_patient_resources(patient_id, "Condition")
    observations = fhir_client.get_patient_resources(patient_id, "Observation")
    medications = fhir_client.get_patient_resources(patient_id, "MedicationRequest")

    events: list[TimelineEvent] = []

    for enc in encounters:
        reason = _extract_display(
            (enc.get("reasonCode") or [{}])[0].get("coding") if enc.get("reasonCode") else None
        )
        type_display = _extract_display(
            (enc.get("type") or [{}])[0].get("coding") if enc.get("type") else None
        )
        events.append(
            TimelineEvent(
                date=_resource_date(enc),
                event_type="Encounter",
                description=reason or type_display or "Encounter",
                resource_id=enc.get("id"),
            )
        )

    for cond in conditions:
        display = _extract_display(cond.get("code", {}).get("coding")) or cond.get("code", {}).get("text", "Condition")
        events.append(
            TimelineEvent(
                date=_resource_date(cond),
                event_type="Condition",
                description=display,
                resource_id=cond.get("id"),
            )
        )

    for obs in observations:
        display = _extract_display(obs.get("code", {}).get("coding")) or "Observation"
        events.append(
            TimelineEvent(
                date=_resource_date(obs),
                event_type="Observation",
                description=display,
                resource_id=obs.get("id"),
            )
        )

    for med in medications:
        display = (
            _extract_display(med.get("medicationCodeableConcept", {}).get("coding"))
            or med.get("medicationCodeableConcept", {}).get("text", "Medication")
        )
        events.append(
            TimelineEvent(
                date=_resource_date(med),
                event_type="MedicationRequest",
                description=display,
                resource_id=med.get("id"),
            )
        )

    events.sort(key=lambda e: e.date or "", reverse=True)
    return PatientTimeline(patient_id=patient_id, events=events)


@router.get("/{patient_id}/resources")
def get_patient_resources(
    patient_id: str,
    fhir_client: FHIRClientDep,
    type: str | None = Query(default=None),
):
    """Return raw FHIR resources for a patient (debug/inspector tab)."""
    resource_types = [type] if type else ["Patient", "Encounter", "Condition", "Observation", "MedicationRequest"]
    result: dict[str, list] = {}
    for rt in resource_types:
        if rt == "Patient":
            try:
                result["Patient"] = [fhir_client.get_resource("Patient", patient_id)]
            except Exception:
                result["Patient"] = []
        else:
            result[rt] = fhir_client.get_patient_resources(patient_id, rt)
    return result
