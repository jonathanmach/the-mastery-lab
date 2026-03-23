import json
import logging

import httpx

logger = logging.getLogger(__name__)


class FHIRClient:
    """Thin HTTP client for a FHIR R4 server (HAPI FHIR or any FHIR-compliant endpoint)."""

    def __init__(self, base_url: str, client: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=httpx.Timeout(10.0, read=120.0))

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert_resource(self, resource_type: str, logical_id: str, resource_dict: dict) -> dict:
        """PUT a resource by logical ID (creates or updates)."""
        url = f"{self.base_url}/{resource_type}/{logical_id}"
        response = self._client.put(
            url,
            content=json.dumps(resource_dict),
            headers={"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        return response.json()

    def post_transaction_bundle(self, bundle_dict: dict) -> dict:
        """POST a FHIR transaction bundle. HAPI resolves urn:uuid: references internally."""
        response = self._client.post(
            self.base_url,
            content=json.dumps(bundle_dict),
            headers={"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_resource(self, resource_type: str, logical_id: str) -> dict:
        """GET a single resource by type and ID."""
        url = f"{self.base_url}/{resource_type}/{logical_id}"
        response = self._client.get(url, headers={"Accept": "application/fhir+json"})
        response.raise_for_status()
        return response.json()

    def search(self, resource_type: str, params: dict) -> dict:
        """GET a search bundle for a resource type with query params."""
        url = f"{self.base_url}/{resource_type}"
        response = self._client.get(url, params=params, headers={"Accept": "application/fhir+json"})
        response.raise_for_status()
        return response.json()

    def get_patient_resources(self, patient_id: str, resource_type: str) -> list[dict]:
        """Fetch all resources of a given type for a patient (handles pagination)."""
        params = {"patient": patient_id, "_count": "100"}
        results: list[dict] = []

        bundle = self.search(resource_type, params)
        while True:
            for entry in bundle.get("entry") or []:
                if entry.get("resource"):
                    results.append(entry["resource"])

            # follow next page link if present
            next_url = next(
                (link["url"] for link in (bundle.get("link") or []) if link.get("relation") == "next"),
                None,
            )
            if not next_url:
                break
            response = self._client.get(next_url, headers={"Accept": "application/fhir+json"})
            response.raise_for_status()
            bundle = response.json()

        return results

    def close(self) -> None:
        self._client.close()
