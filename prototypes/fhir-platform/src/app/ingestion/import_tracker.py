import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import ImportRecord, ImportStatus

logger = logging.getLogger(__name__)


class ImportTracker:
    def __init__(self, session: Session):
        self.session = session

    def record_pending(
        self,
        source_file: str,
        bundle_id: str | None,
        resource_type: str,
        logical_id: str,
    ) -> ImportRecord:
        record = ImportRecord(
            source_file=source_file,
            bundle_id=bundle_id,
            resource_type=resource_type,
            logical_id=logical_id,
            import_status=ImportStatus.pending,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def mark_success(self, record: ImportRecord) -> None:
        record.import_status = ImportStatus.success
        record.import_timestamp = datetime.now(timezone.utc)
        self.session.flush()

    def mark_failed(self, record: ImportRecord, errors: list[str]) -> None:
        record.import_status = ImportStatus.failed
        record.validation_errors = json.dumps(errors)
        record.import_timestamp = datetime.now(timezone.utc)
        self.session.flush()

    def mark_skipped(self, record: ImportRecord) -> None:
        record.import_status = ImportStatus.skipped
        record.import_timestamp = datetime.now(timezone.utc)
        self.session.flush()

    def summary(self) -> dict:
        from sqlalchemy import func, select

        rows = self.session.execute(
            select(ImportRecord.import_status, func.count().label("count")).group_by(ImportRecord.import_status)
        ).all()
        return {row.import_status: row.count for row in rows}
