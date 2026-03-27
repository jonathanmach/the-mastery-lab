from pydantic import BaseModel


class FacetBucket(BaseModel):
    key: str
    display: str | None = None
    count: int


class PatientFacetsResponse(BaseModel):
    gender: list[FacetBucket]
    age_band: list[FacetBucket]
    diagnosis: list[FacetBucket]
    medication: list[FacetBucket]
    recent_encounter: list[FacetBucket]
    observation: list[FacetBucket]


class PatientHit(BaseModel):
    patient_id: str | None
    name: str
    family_name: str | None = None
    given_name: str | None = None
    gender: str | None
    birth_date: str | None
    age_band: str | None
    conditions: list[str]
    condition_codes: list[str]
    medications: list[str]
    medication_codes: list[str]
    last_encounter_date: str | None
    has_active_medication: bool
    has_recent_encounter: bool
    validation_status: str


class PatientSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[PatientHit]


class TimelineEvent(BaseModel):
    date: str | None
    event_type: str
    description: str
    resource_id: str | None


class PatientSummary(BaseModel):
    patient_id: str
    name: str
    gender: str | None
    birth_date: str | None
    age_band: str | None
    address: str | None
    conditions: list[dict]
    medications: list[dict]
    latest_observations: list[dict]
    encounters: list[dict]
    validation_status: str


class PatientTimeline(BaseModel):
    patient_id: str
    events: list[TimelineEvent]
