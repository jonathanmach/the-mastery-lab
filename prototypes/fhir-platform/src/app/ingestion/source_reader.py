import json
from pathlib import Path


def read_bundle_from_file(path: str | Path) -> dict:
    """Read and parse a FHIR bundle JSON file from the local filesystem."""
    bundle_path = Path(path)
    if not bundle_path.exists():
        raise FileNotFoundError(f"Bundle file not found: {bundle_path}")
    with bundle_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_bundle_files(directory: str | Path) -> list[Path]:
    """Return all .json files in a directory, sorted by name."""
    bundle_dir = Path(directory)
    if not bundle_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {bundle_dir}")
    return sorted(bundle_dir.glob("*.json"))
