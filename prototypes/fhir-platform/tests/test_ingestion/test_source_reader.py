import json
from pathlib import Path

import pytest

from app.ingestion.source_reader import list_bundle_files, read_bundle_from_file


def test_read_bundle_from_file(tmp_path, sample_bundle):
    bundle_file = tmp_path / "bundle.json"
    bundle_file.write_text(json.dumps(sample_bundle))
    result = read_bundle_from_file(bundle_file)
    assert result["resourceType"] == "Bundle"
    assert result["id"] == "test-bundle-001"


def test_read_bundle_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_bundle_from_file(tmp_path / "nonexistent.json")


def test_list_bundle_files(tmp_path):
    (tmp_path / "a.json").write_text("{}")
    (tmp_path / "b.json").write_text("{}")
    (tmp_path / "notes.txt").write_text("ignore me")
    files = list_bundle_files(tmp_path)
    assert len(files) == 2
    assert all(f.suffix == ".json" for f in files)


def test_list_bundle_files_not_a_directory(tmp_path):
    with pytest.raises(NotADirectoryError):
        list_bundle_files(tmp_path / "does_not_exist")
