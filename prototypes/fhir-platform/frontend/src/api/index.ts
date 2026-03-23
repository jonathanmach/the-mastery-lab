import type {
  PatientFacets,
  PatientSearchResponse,
  PatientSummary,
  PatientTimeline,
  SearchFilters,
} from './types'

const BASE = '/patients'

function buildQuery(params: Record<string, string | number | boolean | null | undefined>): string {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') {
      q.set(k, String(v))
    }
  }
  return q.toString() ? `?${q}` : ''
}

export async function searchPatients(filters: SearchFilters): Promise<PatientSearchResponse> {
  const qs = buildQuery({
    q: filters.q,
    gender: filters.gender,
    condition: filters.condition,
    medication: filters.medication,
    age_band: filters.age_band,
    recent_encounter: filters.recent_encounter,
    observation: filters.observation,
    obs_min: filters.obs_min,
    obs_max: filters.obs_max,
    page: filters.page,
  })
  const res = await fetch(`${BASE}/search${qs}`)
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  return res.json()
}

export async function getPatientFacets(
  filters: Partial<Omit<SearchFilters, 'q' | 'page'>>
): Promise<PatientFacets> {
  const qs = buildQuery({
    gender: filters.gender,
    condition: filters.condition,
    medication: filters.medication,
    age_band: filters.age_band,
    observation: filters.observation,
  })
  const res = await fetch(`${BASE}/facets${qs}`)
  if (!res.ok) throw new Error(`Facets failed: ${res.status}`)
  return res.json()
}

export async function getPatientSummary(patientId: string): Promise<PatientSummary> {
  const res = await fetch(`${BASE}/${patientId}/summary`)
  if (!res.ok) throw new Error(`Patient not found: ${res.status}`)
  return res.json()
}

export async function getPatientTimeline(patientId: string): Promise<PatientTimeline> {
  const res = await fetch(`${BASE}/${patientId}/timeline`)
  if (!res.ok) throw new Error(`Timeline failed: ${res.status}`)
  return res.json()
}

export async function getPatientResources(
  patientId: string,
  resourceType?: string
): Promise<Record<string, unknown[]>> {
  const qs = resourceType ? `?type=${resourceType}` : ''
  const res = await fetch(`${BASE}/${patientId}/resources${qs}`)
  if (!res.ok) throw new Error(`Resources failed: ${res.status}`)
  return res.json()
}
