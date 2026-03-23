import logging
from datetime import date, datetime, timezone

from opensearchpy import OpenSearch, RequestError

from app.config import settings
from app.ingestion.fhir_client import FHIRClient

logger = logging.getLogger(__name__)

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "patient_id": {"type": "keyword"},
            "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "family_name": {"type": "keyword"},
            "given_name": {"type": "keyword"},
            "gender": {"type": "keyword"},
            "birth_date": {"type": "date"},
            "age_band": {"type": "keyword"},
            "conditions": {"type": "text"},
            "condition_codes": {"type": "keyword"},
            "condition_pairs": {"type": "keyword"},
            "medications": {"type": "text"},
            "medication_codes": {"type": "keyword"},
            "medication_pairs": {"type": "keyword"},
            "observation_codes": {"type": "keyword"},
            "observation_pairs": {"type": "keyword"},
            "obs_values": {"type": "object", "dynamic": True},
            "latest_observations": {"type": "object", "enabled": False},
            "last_encounter_date": {"type": "date"},
            "has_active_medication": {"type": "boolean"},
            "has_recent_encounter": {"type": "boolean"},
            "validation_status": {"type": "keyword"},
        }
    }
}

PAGE_SIZE = 20


def _build_os_client(endpoint: str) -> OpenSearch:
    return OpenSearch(hosts=[endpoint], use_ssl=False, verify_certs=False)


def _age_band(birth_date_str: str | None) -> str | None:
    if not birth_date_str:
        return None
    try:
        bd = date.fromisoformat(birth_date_str)
        today = date.today()
        age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except ValueError:
        return None
    if age < 18:
        return "<18"
    if age < 35:
        return "18-34"
    if age < 50:
        return "35-49"
    if age < 65:
        return "50-64"
    return "65+"


def _validation_status(has_patient: bool, has_encounter: bool, has_condition: bool, has_observation: bool) -> str:
    if not has_patient or not has_encounter:
        return "insufficient"
    if has_condition or has_observation:
        return "usable"
    return "partial"


def _extract_display(coding_list: list | None) -> str | None:
    if not coding_list:
        return None
    for c in coding_list:
        if isinstance(c, dict) and c.get("display"):
            return c["display"]
    return None


def _resource_date(resource: dict) -> str | None:
    for field in ("recordedDate", "onsetDateTime", "effectiveDateTime", "authoredOn", "period"):
        val = resource.get(field)
        if val:
            if isinstance(val, dict):
                return val.get("start")
            return val
    return None


class SearchProjector:
    def __init__(self, client: OpenSearch | None = None, index: str | None = None):
        self._client = client or _build_os_client(settings.opensearch_endpoint)
        self._index = index or settings.opensearch_index
        self._ensure_index()

    def _ensure_index(self) -> None:
        if not self._client.indices.exists(index=self._index):
            try:
                self._client.indices.create(index=self._index, body=INDEX_MAPPING)
                logger.info("Created OpenSearch index: %s", self._index)
            except RequestError as exc:
                # index may have been created concurrently
                logger.warning("Could not create index (may already exist): %s", exc)

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def project_patient(self, patient_id: str, fhir_client: FHIRClient) -> None:
        patient = fhir_client.get_resource("Patient", patient_id)
        encounters = fhir_client.get_patient_resources(patient_id, "Encounter")
        conditions = fhir_client.get_patient_resources(patient_id, "Condition")
        observations = fhir_client.get_patient_resources(patient_id, "Observation")
        medications = fhir_client.get_patient_resources(patient_id, "MedicationRequest")

        doc = self._build_doc(patient, encounters, conditions, observations, medications)
        self._client.index(index=self._index, id=patient_id, body=doc)
        logger.info("Projected patient %s → OpenSearch", patient_id)

    def _build_doc(
        self,
        patient: dict,
        encounters: list[dict],
        conditions: list[dict],
        observations: list[dict],
        medications: list[dict],
    ) -> dict:
        # Name
        names = patient.get("name") or []
        family = names[0].get("family") if names else None
        given_list = names[0].get("given") or [] if names else []
        given = given_list[0] if given_list else None
        full_name = " ".join(filter(None, [given, family])) or patient.get("id", "")

        birth_date = patient.get("birthDate")

        # Conditions
        condition_displays = [
            _extract_display(c.get("code", {}).get("coding")) or c.get("code", {}).get("text", "")
            for c in conditions
        ]
        condition_codes = [
            coding.get("code", "")
            for c in conditions
            for coding in (c.get("code", {}).get("coding") or [])
            if coding.get("code")
        ]
        # "code|display" pairs for faceting with human-readable labels
        _seen_codes: set[str] = set()
        condition_pairs: list[str] = []
        for c in conditions:
            for coding in (c.get("code", {}).get("coding") or []):
                code = coding.get("code", "")
                if code and code not in _seen_codes:
                    display = coding.get("display") or c.get("code", {}).get("text") or code
                    condition_pairs.append(f"{code}|{display}")
                    _seen_codes.add(code)

        # Medications
        med_displays = [
            _extract_display(m.get("medicationCodeableConcept", {}).get("coding"))
            or m.get("medicationCodeableConcept", {}).get("text", "")
            for m in medications
        ]
        med_codes = [
            coding.get("code", "")
            for m in medications
            for coding in (m.get("medicationCodeableConcept", {}).get("coding") or [])
            if coding.get("code")
        ]
        _seen_med_codes: set[str] = set()
        medication_pairs: list[str] = []
        for m in medications:
            for coding in (m.get("medicationCodeableConcept", {}).get("coding") or []):
                code = coding.get("code", "")
                if code and code not in _seen_med_codes:
                    display = (
                        coding.get("display")
                        or m.get("medicationCodeableConcept", {}).get("text")
                        or code
                    )
                    medication_pairs.append(f"{code}|{display}")
                    _seen_med_codes.add(code)
        has_active_med = any(m.get("status") == "active" for m in medications)

        # Encounters
        encounter_dates = sorted(
            filter(None, (_resource_date(e) for e in encounters)),
            reverse=True,
        )
        last_encounter_date = encounter_dates[0][:10] if encounter_dates else None
        has_recent_encounter = False
        if last_encounter_date:
            try:
                delta = date.today() - date.fromisoformat(last_encounter_date)
                has_recent_encounter = delta.days <= 365
            except ValueError:
                pass

        # Observations (latest per LOINC code)
        latest_observations: dict[str, dict] = {}
        for obs in sorted(observations, key=lambda o: _resource_date(o) or "", reverse=True):
            for coding in obs.get("code", {}).get("coding") or []:
                code = coding.get("code")
                if code and code not in latest_observations:
                    value = obs.get("valueQuantity") or obs.get("valueString") or obs.get("valueCodeableConcept")
                    latest_observations[code] = {
                        "display": coding.get("display", code),
                        "value": value,
                        "date": _resource_date(obs),
                    }

        observation_pairs = [
            f"{code}|{v['display']}" for code, v in latest_observations.items()
        ]

        obs_values: dict[str, float] = {}
        for code, obs_data in latest_observations.items():
            raw = obs_data.get("value")
            if isinstance(raw, dict):
                try:
                    obs_values[code.replace("-", "_")] = float(raw["value"])
                except (KeyError, TypeError, ValueError):
                    pass

        return {
            "patient_id": patient.get("id"),
            "name": full_name,
            "family_name": family,
            "given_name": given,
            "gender": patient.get("gender"),
            "birth_date": birth_date,
            "age_band": _age_band(birth_date),
            "conditions": condition_displays,
            "condition_codes": list(dict.fromkeys(condition_codes)),
            "condition_pairs": condition_pairs,
            "medications": med_displays,
            "medication_codes": list(dict.fromkeys(med_codes)),
            "medication_pairs": medication_pairs,
            "observation_codes": list(latest_observations.keys()),
            "observation_pairs": observation_pairs,
            "obs_values": obs_values,
            "latest_observations": latest_observations,
            "last_encounter_date": last_encounter_date,
            "has_active_medication": has_active_med,
            "has_recent_encounter": has_recent_encounter,
            "validation_status": _validation_status(
                has_patient=True,
                has_encounter=bool(encounters),
                has_condition=bool(conditions),
                has_observation=bool(observations),
            ),
        }

    # ------------------------------------------------------------------
    # Search + facets
    # ------------------------------------------------------------------

    def search(
        self,
        q: str = "",
        gender: str | None = None,
        condition: str | None = None,
        medication: str | None = None,
        age_band: str | None = None,
        recent_encounter: bool | None = None,
        observation: str | None = None,
        obs_min: float | None = None,
        obs_max: float | None = None,
        page: int = 1,
    ) -> dict:
        filters = [{"term": {"validation_status": "usable"}}]

        if gender:
            filters.append({"term": {"gender": gender}})
        if condition:
            filters.append({"term": {"condition_codes": condition}})
        if medication:
            filters.append({"term": {"medication_codes": medication}})
        if age_band:
            filters.append({"term": {"age_band": age_band}})
        if recent_encounter is not None:
            filters.append({"term": {"has_recent_encounter": recent_encounter}})
        if observation:
            filters.append({"term": {"observation_codes": observation}})
            if obs_min is not None or obs_max is not None:
                range_clause: dict = {}
                if obs_min is not None:
                    range_clause["gte"] = obs_min
                if obs_max is not None:
                    range_clause["lte"] = obs_max
                filters.append({"range": {f"obs_values.{observation.replace('-', '_')}": range_clause}})

        query: dict = {"bool": {"filter": filters}}
        if q:
            query["bool"]["must"] = [{"multi_match": {"query": q, "fields": ["name", "family_name", "given_name"]}}]

        body = {
            "query": query,
            "from": (page - 1) * PAGE_SIZE,
            "size": PAGE_SIZE,
            "sort": [{"family_name": {"order": "asc"}}],
        }
        response = self._client.search(index=self._index, body=body)
        hits = response["hits"]
        return {
            "total": hits["total"]["value"],
            "page": page,
            "page_size": PAGE_SIZE,
            "results": [h["_source"] for h in hits["hits"]],
        }

    def facets(
        self,
        gender: str | None = None,
        condition: str | None = None,
        medication: str | None = None,
        age_band: str | None = None,
        observation: str | None = None,
    ) -> dict:
        filters = [{"term": {"validation_status": "usable"}}]
        if gender:
            filters.append({"term": {"gender": gender}})
        if condition:
            filters.append({"term": {"condition_codes": condition}})
        if medication:
            filters.append({"term": {"medication_codes": medication}})
        if age_band:
            filters.append({"term": {"age_band": age_band}})
        if observation:
            filters.append({"term": {"observation_codes": observation}})

        body = {
            "query": {"bool": {"filter": filters}},
            "size": 0,
            "aggs": {
                "gender": {"terms": {"field": "gender", "size": 10}},
                "age_band": {"terms": {"field": "age_band", "size": 10}},
                "diagnosis": {"terms": {"field": "condition_pairs", "size": 30}},
                "medication": {"terms": {"field": "medication_pairs", "size": 30}},
                "recent_encounter": {"terms": {"field": "has_recent_encounter", "size": 2}},
                "observation": {"terms": {"field": "observation_pairs", "size": 50}},
            },
        }
        response = self._client.search(index=self._index, body=body)
        aggs = response["aggregations"]

        def buckets(agg_name: str) -> list[dict]:
            return [{"key": str(b["key"]), "count": b["doc_count"]} for b in aggs[agg_name]["buckets"]]

        def pair_buckets(agg_name: str) -> list[dict]:
            result = []
            for b in aggs[agg_name]["buckets"]:
                pair = str(b["key"])
                if "|" in pair:
                    code, display = pair.split("|", 1)
                else:
                    code = display = pair
                result.append({"key": code, "display": display, "count": b["doc_count"]})
            return result

        return {
            "gender": buckets("gender"),
            "age_band": buckets("age_band"),
            "diagnosis": pair_buckets("diagnosis"),
            "medication": pair_buckets("medication"),
            "recent_encounter": buckets("recent_encounter"),
            "observation": pair_buckets("observation"),
        }
