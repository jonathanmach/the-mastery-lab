#!/usr/bin/env python3
"""CLI: ingest all Synthea bundle files from a local directory into HAPI FHIR,
then project each patient into the OpenSearch index.

Usage:
    uv run python scripts/ingest_bundles.py [--dir ./data/synthea_bundles]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# ensure src/ is on path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import settings
from app.db.models import ImportStatus
from app.db.session import get_session, init_db
from app.ingestion.bundle_parser import parse_bundle
from app.ingestion.fhir_client import FHIRClient
from app.ingestion.import_tracker import ImportTracker
from app.ingestion.source_reader import list_bundle_files, read_bundle_from_file
from app.projection.search_projector import SearchProjector

logging.basicConfig(level=settings.log_level, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("ingest")


def ingest(bundles_dir: str) -> None:
    init_db(settings.database_url)
    fhir_client = FHIRClient(base_url=settings.fhir_base_url)
    projector = SearchProjector()

    bundle_files = list_bundle_files(bundles_dir)
    if not bundle_files:
        logger.warning("No .json files found in %s", bundles_dir)
        return

    logger.info("Found %d bundle file(s) in %s", len(bundle_files), bundles_dir)

    total_success = total_failed = total_skipped = 0
    projected_patients: set[str] = set()

    for bundle_path in bundle_files:
        logger.info("Processing %s", bundle_path.name)
        try:
            raw = read_bundle_from_file(bundle_path)
            parse_result = parse_bundle(raw)
        except Exception as exc:
            logger.error("Failed to parse %s: %s", bundle_path.name, exc)
            continue

        patient_id: str | None = None

        with get_session(settings.database_url) as session:
            tracker = ImportTracker(session)

            for res in parse_result.resources:
                record = tracker.record_pending(
                    source_file=bundle_path.name,
                    bundle_id=parse_result.bundle_id,
                    resource_type=res.resource_type,
                    logical_id=res.logical_id,
                )

                if res.error:
                    tracker.mark_failed(record, [res.error])
                    total_failed += 1
                    continue

                try:
                    resource_dict = json.loads(res.resource.model_dump_json(exclude_none=True))
                    fhir_client.upsert_resource(res.resource_type, res.logical_id, resource_dict)
                    tracker.mark_success(record)
                    total_success += 1
                    if res.resource_type == "Patient":
                        patient_id = res.logical_id
                except Exception as exc:
                    logger.warning("Failed to upsert %s/%s: %s", res.resource_type, res.logical_id, exc)
                    tracker.mark_failed(record, [str(exc)])
                    total_failed += 1

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
