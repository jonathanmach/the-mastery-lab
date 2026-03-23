#!/usr/bin/env python3
"""CLI: ingest all Synthea bundle files from a local directory into HAPI FHIR,
then project each patient into the OpenSearch index.

Usage:
    uv run python scripts/ingest_bundles.py [--dir ./data/synthea_bundles]
"""

import argparse
import json
import logging
import re
import sys
import uuid
from pathlib import Path

# ensure src/ is on path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import settings
from app.db.session import get_session, init_db
from app.ingestion.bundle_parser import parse_bundle, prepare_bundle_for_upsert
from app.ingestion.fhir_client import FHIRClient
from app.ingestion.import_tracker import ImportTracker
from app.ingestion.source_reader import list_bundle_files, read_bundle_from_file
from app.projection.search_projector import SearchProjector

logging.basicConfig(level=settings.log_level, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("ingest")

NPI_PATTERN = re.compile(r"Practitioner\?identifier=http://hl7\.org/fhir/sid/us-npi\|(\d+)")


def _find_patient_id(raw: dict) -> str | None:
    for entry in raw.get("entry") or []:
        resource = entry.get("resource") or {}
        if resource.get("resourceType") == "Patient":
            return resource.get("id")
    return None


def _load_hospital_bundle(bundle_path: Path, fhir_client: FHIRClient) -> None:
    """POST the hospitalInformation batch bundle to seed Organizations and Locations."""
    logger.info("Loading hospital bundle: %s", bundle_path.name)
    raw = read_bundle_from_file(bundle_path)
    try:
        fhir_client.post_transaction_bundle(raw)
        logger.info("Hospital bundle loaded successfully")
    except Exception as exc:
        logger.warning("Hospital bundle load failed (may already exist): %s", exc)


def _ensure_practitioners(bundle_files: list[Path], fhir_client: FHIRClient) -> None:
    """Extract unique NPI identifiers from all patient bundles and pre-create stub Practitioners."""
    npis: set[str] = set()
    for f in bundle_files:
        text = f.read_text()
        npis.update(NPI_PATTERN.findall(text))

    if not npis:
        return

    logger.info("Pre-creating %d stub Practitioner(s)", len(npis))
    entries = []
    for npi in npis:
        resource_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"npi:{npi}"))
        entries.append({
            "fullUrl": f"urn:uuid:{resource_id}",
            "resource": {
                "resourceType": "Practitioner",
                "id": resource_id,
                "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": npi}],
            },
            "request": {
                "method": "PUT",
                "url": f"Practitioner/{resource_id}",
                "ifNoneExist": f"identifier=http://hl7.org/fhir/sid/us-npi|{npi}",
            },
        })

    # POST in batches of 200
    batch_size = 200
    for i in range(0, len(entries), batch_size):
        batch = {
            "resourceType": "Bundle",
            "type": "batch",
            "entry": entries[i : i + batch_size],
        }
        try:
            fhir_client.post_transaction_bundle(batch)
        except Exception as exc:
            logger.warning("Practitioner pre-create batch failed: %s", exc)


def ingest(bundles_dir: str) -> None:
    init_db(settings.database_url)
    fhir_client = FHIRClient(base_url=settings.fhir_base_url)
    projector = SearchProjector()

    all_files = list_bundle_files(bundles_dir)
    if not all_files:
        logger.warning("No .json files found in %s", bundles_dir)
        return

    # Separate infrastructure bundles (hospital/practitioner info) from patient bundles
    infra_keywords = ("hospital", "practitioner")
    hospital_files = [f for f in all_files if any(k in f.name.lower() for k in infra_keywords)]
    patient_files = [f for f in all_files if not any(k in f.name.lower() for k in infra_keywords)]

    logger.info(
        "Found %d bundle file(s): %d hospital, %d patient",
        len(all_files),
        len(hospital_files),
        len(patient_files),
    )

    # Step 1: load infrastructure bundles (Organizations, Locations, Practitioners)
    for hf in hospital_files:
        _load_hospital_bundle(hf, fhir_client)

    # Step 2: ingest patient bundles as transactions
    total_success = total_failed = 0
    projected_patients: set[str] = set()

    for bundle_path in patient_files:
        logger.info("Processing %s", bundle_path.name)
        try:
            raw = read_bundle_from_file(bundle_path)
        except Exception as exc:
            logger.error("Failed to read %s: %s", bundle_path.name, exc)
            total_failed += 1
            continue

        patient_id = _find_patient_id(raw)

        # Validate individual resources and record parse-level errors
        parse_result = None
        try:
            parse_result = parse_bundle(raw)
        except Exception as exc:
            logger.error("Failed to parse %s: %s", bundle_path.name, exc)

        if parse_result:
            with get_session(settings.database_url) as session:
                tracker = ImportTracker(session)
                for res in parse_result.resources:
                    if res.error:
                        record = tracker.record_pending(
                            source_file=bundle_path.name,
                            bundle_id=parse_result.bundle_id,
                            resource_type=res.resource_type,
                            logical_id=res.logical_id,
                        )
                        tracker.mark_failed(record, [res.error])

        # POST the whole bundle as a transaction
        try:
            bundle_to_post = prepare_bundle_for_upsert(raw)
            fhir_client.post_transaction_bundle(bundle_to_post)
            total_success += 1
        except Exception as exc:
            logger.warning("Failed to post bundle %s: %s", bundle_path.name, exc)
            total_failed += 1
            continue

        if patient_id and patient_id not in projected_patients:
            try:
                projector.project_patient(patient_id, fhir_client)
                projected_patients.add(patient_id)
            except Exception as exc:
                logger.warning("Projection failed for patient %s: %s", patient_id, exc)

    fhir_client.close()

    logger.info(
        "Ingestion complete — success: %d  failed: %d  projected patients: %d",
        total_success,
        total_failed,
        len(projected_patients),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Synthea FHIR bundles into HAPI FHIR + OpenSearch")
    parser.add_argument(
        "--dir",
        default=settings.synthea_bundles_dir,
        help="Directory containing Synthea bundle .json files (default: %(default)s)",
    )
    args = parser.parse_args()
    ingest(args.dir)


if __name__ == "__main__":
    main()
