import copy
import logging
from dataclasses import dataclass, field

from fhir.resources.R4B import get_fhir_model_class
from pydantic import ValidationError

logger = logging.getLogger(__name__)

SUPPORTED_RESOURCE_TYPES = frozenset(
    {"Patient", "Encounter", "Condition", "Observation", "MedicationRequest"}
)


@dataclass
class ResourceResult:
    resource_type: str
    logical_id: str
    resource: object | None  # fhir.resources R4B model instance
    error: str | None


@dataclass
class ParseResult:
    bundle_id: str | None
    resources: list[ResourceResult] = field(default_factory=list)


def prepare_bundle_for_upsert(raw: dict) -> dict:
    """Rewrite transaction bundle entries from POST to PUT with resource IDs.

    Synthea generates bundles with POST requests and urn:uuid: fullUrls. Rewriting to
    PUT preserves Synthea UUIDs so resources are created with known IDs. HAPI still
    resolves the urn:uuid: references internally during transaction processing.
    """
    bundle = copy.deepcopy(raw)
    for entry in bundle.get("entry") or []:
        resource = entry.get("resource") or {}
        resource_id = resource.get("id")
        resource_type = resource.get("resourceType")
        request = entry.get("request") or {}
        if resource_id and resource_type and request.get("method") == "POST":
            entry["request"] = {"method": "PUT", "url": f"{resource_type}/{resource_id}"}
    return bundle


def parse_bundle(raw: dict) -> ParseResult:
    """Parse a raw FHIR bundle dict into typed resource results.

    The bundle envelope is parsed as plain dict (lenient).
    Each supported resource is individually validated with fhir.resources R4B.
    Per-resource ValidationErrors are captured rather than raising, so one bad
    resource does not abort the whole bundle.
    """
    if raw.get("resourceType") != "Bundle":
        raise ValueError(f"Invalid FHIR Bundle envelope: resourceType is '{raw.get('resourceType')}'")

    bundle_id = raw.get("id")
    result = ParseResult(bundle_id=bundle_id)

    for entry in raw.get("entry") or []:
        resource_dict = entry.get("resource")
        if not resource_dict:
            continue

        rt = resource_dict.get("resourceType")
        if rt not in SUPPORTED_RESOURCE_TYPES:
            continue

        logical_id = resource_dict.get("id")
        if not logical_id:
            logger.warning("Skipping %s resource with no id", rt)
            continue

        try:
            model_class = get_fhir_model_class(rt)
            resource = model_class.model_validate(resource_dict)
            result.resources.append(ResourceResult(resource_type=rt, logical_id=logical_id, resource=resource, error=None))
        except (ValidationError, KeyError) as exc:
            logger.warning("Validation error for %s/%s: %s", rt, logical_id, exc)
            result.resources.append(ResourceResult(resource_type=rt, logical_id=logical_id, resource=None, error=str(exc)))

    return result
