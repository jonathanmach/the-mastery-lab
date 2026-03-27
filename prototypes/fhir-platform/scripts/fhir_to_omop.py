#!/usr/bin/env python3
"""
ETL: HAPI FHIR → OMOP CDM v5.4

Reads all patients from HAPI FHIR using FHIRClient, transforms each resource
type to the corresponding OMOP CDM table, and writes to PostgreSQL.

Concept IDs are derived from FHIR coding (system + code + display) and stored in
the concept table so clinical tables can JOIN for human-readable labels.

Usage:
    uv run python scripts/fhir_to_omop.py [--fhir-url URL] [--omop-url DSN] [--page-size N] [--overwrite]

Example:
    uv run python scripts/fhir_to_omop.py \\
        --fhir-url http://localhost:8081/fhir \\
        --omop-url postgresql://omop:omop_secret@localhost:5435/omop \\
        --overwrite
"""

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import settings
from app.ingestion.fhir_client import FHIRClient
from app.omop.models import (
    Concept,
    ConditionOccurrence,
    DrugExposure,
    Measurement,
    Observation,
    ObservationPeriod,
    Person,
    VisitOccurrence,
)
from app.omop.session import get_omop_session, init_omop_db

logging.basicConfig(level=settings.log_level, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("fhir_to_omop")


# ---------------------------------------------------------------------------
# FHIR pagination
# ---------------------------------------------------------------------------


def iter_all_patients(fhir_client: FHIRClient, page_size: int = 100):
    """Yield individual Patient resource dicts from HAPI FHIR, handling pagination."""
    params = {"_count": str(page_size)}
    bundle = fhir_client.search("Patient", params)
    while True:
        for entry in bundle.get("entry") or []:
            resource = entry.get("resource")
            if resource and resource.get("resourceType") == "Patient":
                yield resource

        next_url = next(
            (link["url"] for link in (bundle.get("link") or []) if link.get("relation") == "next"),
            None,
        )
        if not next_url:
            break
        response = fhir_client._client.get(next_url, headers={"Accept": "application/fhir+json"})
        response.raise_for_status()
        bundle = response.json()


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

_FHIR_SYSTEM_TO_VOCAB: dict[str, str] = {
    "http://snomed.info/sct": "SNOMED",
    "http://www.nlm.nih.gov/research/umls/rxnorm": "RxNorm",
    "http://loinc.org": "LOINC",
    "http://hl7.org/fhir/sid/icd-10-cm": "ICD10CM",
    "http://hl7.org/fhir/sid/icd-10": "ICD10",
}


def _extract_concept_info(codeable_concept: dict | None) -> tuple[str, str, str] | None:
    """Return (vocabulary_id, concept_code, display) from the first coding with a code, or None."""
    if not codeable_concept:
        return None
    for coding in codeable_concept.get("coding") or []:
        code = coding.get("code")
        if not code:
            continue
        system = coding.get("system", "")
        vocab_id = _FHIR_SYSTEM_TO_VOCAB.get(system, "Unknown")
        display = coding.get("display") or codeable_concept.get("text") or code
        return (vocab_id, code, str(display)[:500])
    return None


def _parse_birth_date(birth_date_str: str | None) -> tuple[int, int | None, int | None]:
    """Parse FHIR birthDate ('YYYY', 'YYYY-MM', or 'YYYY-MM-DD') → (year, month, day)."""
    if not birth_date_str:
        return (1900, None, None)
    parts = birth_date_str.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else None
    day = int(parts[2]) if len(parts) > 2 else None
    return (year, month, day)


def _map_gender_concept(gender: str) -> int:
    """Map FHIR gender string to OMOP concept ID. 0 = unmapped."""
    return {"male": 8507, "female": 8532}.get(gender.lower(), 0)


def _parse_date(date_str: str | None) -> date | None:
    """Parse ISO date/datetime string to date, stripping the time component."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str[:10])
    except ValueError:
        return None


def _extract_period_dates(resource: dict) -> tuple[date | None, date | None]:
    """Extract start/end dates from a FHIR resource's period, onset, or recorded fields."""
    period = resource.get("period")
    if period:
        return _parse_date(period.get("start")), _parse_date(period.get("end"))
    onset = resource.get("onsetDateTime") or resource.get("recordedDate")
    abatement = resource.get("abatementDateTime")
    return _parse_date(onset), _parse_date(abatement)


def _encounter_fhir_id(reference_str: str | None) -> str | None:
    """Parse 'Encounter/abc-123' → 'abc-123'."""
    if not reference_str:
        return None
    return reference_str.rsplit("/", 1)[-1] if "/" in reference_str else reference_str


# ---------------------------------------------------------------------------
# Concept table management
# ---------------------------------------------------------------------------


def get_or_create_concept(
    session,
    concept_map: dict[tuple[str, str], int],
    vocabulary_id: str,
    concept_code: str,
    display: str,
    domain_id: str,
) -> int:
    """Return concept_id for this (vocabulary_id, concept_code), inserting if new."""
    key = (vocabulary_id, concept_code)
    if key in concept_map:
        return concept_map[key]

    # Check DB in case this is a resumed run (no --overwrite)
    existing = session.query(Concept).filter_by(
        vocabulary_id=vocabulary_id, concept_code=concept_code
    ).first()
    if existing:
        concept_map[key] = existing.concept_id
        return existing.concept_id

    concept = Concept(
        concept_name=display,
        domain_id=domain_id,
        vocabulary_id=vocabulary_id,
        concept_code=concept_code,
    )
    session.add(concept)
    session.flush()  # get auto-generated concept_id
    concept_map[key] = concept.concept_id
    return concept.concept_id


# ---------------------------------------------------------------------------
# ETL core
# ---------------------------------------------------------------------------


def get_or_create_person(session, patient: dict) -> Person:
    """Upsert a Person row. Returns the ORM instance with person_id populated."""
    fhir_id = patient["id"]
    existing = session.query(Person).filter_by(person_source_value=fhir_id).first()
    if existing:
        return existing

    year, month, day = _parse_birth_date(patient.get("birthDate"))
    gender = patient.get("gender", "unknown")

    person = Person(
        gender_concept_id=_map_gender_concept(gender),
        year_of_birth=year,
        month_of_birth=month,
        day_of_birth=day,
        race_concept_id=0,
        ethnicity_concept_id=0,
        person_source_value=fhir_id,
        gender_source_value=gender,
    )
    session.add(person)
    session.flush()  # populate auto-generated person_id before downstream FK inserts
    return person


def etl_patient(
    fhir_client: FHIRClient,
    session,
    patient: dict,
    visit_id_map: dict[str, int],
    concept_map: dict[tuple[str, str], int],
) -> None:
    """ETL a single patient. Writes to session but does not commit."""
    person = get_or_create_person(session, patient)
    patient_id = patient["id"]

    # --- Encounters → visit_occurrence ---
    encounters = fhir_client.get_patient_resources(patient_id, "Encounter")
    encounter_dates: list[date] = []

    for enc in encounters:
        fhir_enc_id = enc.get("id")
        start, end = _extract_period_dates(enc)
        if not start:
            logger.debug("Encounter %s has no start date; skipping", fhir_enc_id)
            continue
        encounter_dates.append(start)

        visit = VisitOccurrence(
            person_id=person.person_id,
            visit_concept_id=0,
            visit_start_date=start,
            visit_end_date=end,
            visit_type_concept_id=32817,
            visit_source_value=fhir_enc_id or "",
        )
        session.add(visit)
        session.flush()  # populate visit_occurrence_id for FK lookups below

        if fhir_enc_id:
            visit_id_map[fhir_enc_id] = visit.visit_occurrence_id

    # --- Observation period (min/max of all encounter start dates) ---
    if encounter_dates:
        session.add(ObservationPeriod(
            person_id=person.person_id,
            observation_period_start_date=min(encounter_dates),
            observation_period_end_date=max(encounter_dates),
            period_type_concept_id=32817,
        ))

    # --- Conditions → condition_occurrence ---
    for cond in fhir_client.get_patient_resources(patient_id, "Condition"):
        start, end = _extract_period_dates(cond)
        if not start:
            continue
        enc_ref = _encounter_fhir_id((cond.get("encounter") or {}).get("reference"))
        c_info = _extract_concept_info(cond.get("code"))
        c_concept_id = get_or_create_concept(session, concept_map, *c_info, "Condition") if c_info else 0
        session.add(ConditionOccurrence(
            person_id=person.person_id,
            condition_concept_id=c_concept_id,
            condition_start_date=start,
            condition_end_date=end,
            condition_type_concept_id=32817,
            condition_source_value=c_info[1] if c_info else None,  # raw code
            visit_occurrence_id=visit_id_map.get(enc_ref) if enc_ref else None,
        ))

    # --- MedicationRequests → drug_exposure ---
    for med in fhir_client.get_patient_resources(patient_id, "MedicationRequest"):
        authored_on = _parse_date(med.get("authoredOn"))
        if not authored_on:
            continue
        enc_ref = _encounter_fhir_id((med.get("encounter") or {}).get("reference"))
        dispense = med.get("dispenseRequest") or {}
        validity = dispense.get("validityPeriod") or {}
        d_info = _extract_concept_info(med.get("medicationCodeableConcept"))
        d_concept_id = get_or_create_concept(session, concept_map, *d_info, "Drug") if d_info else 0
        session.add(DrugExposure(
            person_id=person.person_id,
            drug_concept_id=d_concept_id,
            drug_exposure_start_date=authored_on,
            drug_exposure_end_date=_parse_date(validity.get("end")),
            drug_type_concept_id=32817,
            drug_source_value=d_info[1] if d_info else None,  # raw code
            visit_occurrence_id=visit_id_map.get(enc_ref) if enc_ref else None,
        ))

    # --- Observations → measurement (quantitative) or observation (qualitative) ---
    for obs in fhir_client.get_patient_resources(patient_id, "Observation"):
        obs_date = _parse_date(
            obs.get("effectiveDateTime") or (obs.get("effectivePeriod") or {}).get("start")
        )
        if not obs_date:
            continue
        enc_ref = _encounter_fhir_id((obs.get("encounter") or {}).get("reference"))
        visit_occurrence_id = visit_id_map.get(enc_ref) if enc_ref else None
        o_info = _extract_concept_info(obs.get("code"))

        value_quantity = obs.get("valueQuantity")
        if value_quantity and "value" in value_quantity:
            m_concept_id = get_or_create_concept(session, concept_map, *o_info, "Measurement") if o_info else 0
            try:
                numeric_value = float(value_quantity["value"])
            except (TypeError, ValueError):
                numeric_value = None
            session.add(Measurement(
                person_id=person.person_id,
                measurement_concept_id=m_concept_id,
                measurement_date=obs_date,
                measurement_type_concept_id=32817,
                value_as_number=numeric_value,
                unit_concept_id=0,
                measurement_source_value=o_info[1] if o_info else None,
                visit_occurrence_id=visit_occurrence_id,
            ))
        else:
            ob_concept_id = get_or_create_concept(session, concept_map, *o_info, "Observation") if o_info else 0
            value_str = obs.get("valueString") or _extract_concept_info(obs.get("valueCodeableConcept"))
            if isinstance(value_str, tuple):
                value_str = value_str[2]  # use display from valueCodeableConcept
            session.add(Observation(
                person_id=person.person_id,
                observation_concept_id=ob_concept_id,
                observation_date=obs_date,
                observation_type_concept_id=32817,
                value_as_string=str(value_str)[:255] if value_str else None,
                observation_source_value=o_info[1] if o_info else None,
                visit_occurrence_id=visit_occurrence_id,
            ))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_etl(fhir_url: str, omop_url: str, page_size: int = 100, overwrite: bool = False) -> None:
    logger.info("Initialising OMOP schema at %s (overwrite=%s)", omop_url, overwrite)
    init_omop_db(omop_url, overwrite=overwrite)

    # Pre-load any existing concepts so re-runs don't re-query or duplicate
    concept_map: dict[tuple[str, str], int] = {}
    with get_omop_session(omop_url) as session:
        for c in session.query(Concept).all():
            concept_map[(c.vocabulary_id, c.concept_code)] = c.concept_id
    logger.info("Pre-loaded %d concepts from DB", len(concept_map))

    fhir_client = FHIRClient(base_url=fhir_url)
    total_patients = 0
    total_errors = 0

    for patient in iter_all_patients(fhir_client, page_size=page_size):
        fhir_id = patient.get("id", "<unknown>")
        logger.info("Processing patient %s", fhir_id)
        visit_id_map: dict[str, int] = {}
        try:
            with get_omop_session(omop_url) as session:
                etl_patient(fhir_client, session, patient, visit_id_map, concept_map)
            total_patients += 1
        except Exception as exc:
            logger.error("ETL failed for patient %s: %s", fhir_id, exc)
            total_errors += 1

    fhir_client.close()
    logger.info(
        "ETL complete — patients: %d  errors: %d  concepts: %d",
        total_patients,
        total_errors,
        len(concept_map),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL FHIR → OMOP CDM v5.4")
    parser.add_argument("--fhir-url", default=settings.fhir_base_url)
    parser.add_argument(
        "--omop-url",
        default=settings.omop_database_url or "postgresql://omop:omop_secret@localhost:5435/omop",
    )
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--overwrite", action="store_true",
                        help="Drop and recreate OMOP tables before loading")
    args = parser.parse_args()
    run_etl(fhir_url=args.fhir_url, omop_url=args.omop_url,
            page_size=args.page_size, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
