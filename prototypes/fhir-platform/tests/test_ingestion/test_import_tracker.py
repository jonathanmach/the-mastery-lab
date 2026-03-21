from app.db.models import ImportStatus
from app.ingestion.import_tracker import ImportTracker


def test_record_pending(db_session):
    tracker = ImportTracker(db_session)
    rec = tracker.record_pending("bundle.json", "bundle-001", "Patient", "patient-001")
    assert rec.import_status == ImportStatus.pending
    assert rec.source_file == "bundle.json"
    assert rec.logical_id == "patient-001"


def test_mark_success(db_session):
    tracker = ImportTracker(db_session)
    rec = tracker.record_pending("bundle.json", None, "Patient", "p-1")
    tracker.mark_success(rec)
    assert rec.import_status == ImportStatus.success
    assert rec.import_timestamp is not None


def test_mark_failed(db_session):
    tracker = ImportTracker(db_session)
    rec = tracker.record_pending("bundle.json", None, "Condition", "c-1")
    tracker.mark_failed(rec, ["field X missing", "invalid code"])
    assert rec.import_status == ImportStatus.failed
    import json
    errors = json.loads(rec.validation_errors)
    assert "field X missing" in errors


def test_summary(db_session):
    tracker = ImportTracker(db_session)
    r1 = tracker.record_pending("b.json", None, "Patient", "p-1")
    r2 = tracker.record_pending("b.json", None, "Condition", "c-1")
    tracker.mark_success(r1)
    tracker.mark_failed(r2, ["err"])
    db_session.commit()

    summary = tracker.summary()
    assert summary[ImportStatus.success] == 1
    assert summary[ImportStatus.failed] == 1
