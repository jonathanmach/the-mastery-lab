import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { searchPatients, getPatientFacets } from '../api'
import type { PatientFacets, PatientHit, SearchFilters } from '../api/types'

export const usePatientSearchStore = defineStore('patientSearch', () => {
  const results = ref<PatientHit[]>([])
  const total = ref(0)
  const facets = ref<PatientFacets | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const filters = reactive<SearchFilters>({
    q: '',
    gender: null,
    condition: null,
    medication: null,
    age_band: null,
    recent_encounter: null,
    page: 1,
  })

  async function fetchResults() {
    loading.value = true
    error.value = null
    try {
      const [searchResp, facetsResp] = await Promise.all([
        searchPatients(filters),
        getPatientFacets(filters),
      ])
      results.value = searchResp.results
      total.value = searchResp.total
      facets.value = facetsResp
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  function setFilter<K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) {
    filters[key] = value
    filters.page = 1
    fetchResults()
  }

  function clearFilters() {
    filters.q = ''
    filters.gender = null
    filters.condition = null
    filters.medication = null
    filters.age_band = null
    filters.recent_encounter = null
    filters.page = 1
    fetchResults()
  }

  function nextPage() {
    filters.page++
    fetchResults()
  }

  function prevPage() {
    if (filters.page > 1) {
      filters.page--
      fetchResults()
    }
  }

  return { results, total, facets, loading, error, filters, fetchResults, setFilter, clearFilters, nextPage, prevPage }
})
