export interface FacetBucket {
  key: string
  count: number
}

export interface PatientFacets {
  gender: FacetBucket[]
  age_band: FacetBucket[]
  diagnosis: FacetBucket[]
  medication: FacetBucket[]
  recent_encounter: FacetBucket[]
}

export interface PatientHit {
  patient_id: string
  name: string
  family_name: string | null
  given_name: string | null
  gender: string | null
  birth_date: string | null
  age_band: string | null
  conditions: string[]
  condition_codes: string[]
  medications: string[]
  medication_codes: string[]
  last_encounter_date: string | null
  has_active_medication: boolean
  has_recent_encounter: boolean
  validation_status: string
}

export interface PatientSearchResponse {
  total: number
  page: number
  page_size: number
  results: PatientHit[]
}

export interface TimelineEvent {
  date: string | null
  event_type: string
  description: string
  resource_id: string | null
}

export interface PatientTimeline {
  patient_id: string
  events: TimelineEvent[]
}

export interface PatientSummary {
  patient_id: string
  name: string
  gender: string | null
  birth_date: string | null
  age_band: string | null
  address: string | null
  conditions: Record<string, unknown>[]
  medications: Record<string, unknown>[]
  latest_observations: Array<{ code: string; display: string; value: unknown; date: string | null }>
  validation_status: string
}

export interface SearchFilters {
  q: string
  gender: string | null
  condition: string | null
  medication: string | null
  age_band: string | null
  recent_encounter: boolean | null
  page: number
}
