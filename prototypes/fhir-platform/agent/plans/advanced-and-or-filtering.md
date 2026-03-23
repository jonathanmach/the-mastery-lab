# Advanced AND/OR Filtering

## Context
Currently all filters are single-select and implicitly ANDed. The user wants to select multiple values within a dimension (e.g., Hypertension OR Diabetes) and control whether the match is ANY or ALL. Cross-dimension logic stays as AND (standard faceted search behaviour).

## Scope
- Multi-select for `conditions`, `medications`, `observations` dimensions
- Per-dimension AND/OR toggle (appears when ≥2 items selected)
- All other dimensions (`gender`, `age_band`, `recent_encounter`) stay single-select — no change needed

---

## Implementation Steps

### Step 1 — `search_projector.py`
Add module-level helper above the class (matches existing pattern of `_age_band`, etc.):
```python
def _multi_filter(field: str, codes: list[str], op: str) -> dict:
    if len(codes) == 1:
        return {"term": {field: codes[0]}}
    if op == "and":
        return {"bool": {"filter": [{"term": {field: c}} for c in codes]}}
    return {"terms": {field: codes}}  # OR default
```

Update `search()` signature — replace `condition`, `medication`, `observation` scalars:
```python
conditions: list[str] | None = None,
condition_op: str = "or",
medications: list[str] | None = None,
medication_op: str = "or",
observations: list[str] | None = None,
observation_op: str = "or",
```

Replace the three `if condition:` filter blocks:
```python
if conditions:
    filters.append(_multi_filter("condition_codes", conditions, condition_op))
if medications:
    filters.append(_multi_filter("medication_codes", medications, medication_op))
if observations:
    filters.append(_multi_filter("observation_codes", observations, observation_op))
    if obs_min is not None or obs_max is not None:
        obs_code = observations[0].replace("-", "_")
        ...range filter using obs_code...
```

Apply same signature changes to `facets()` method.

### Step 2 — `src/app/api/routes.py`
Replace scalar `condition`/`medication`/`observation` Query params with lists:
```python
from typing import Annotated
conditions: Annotated[list[str], Query()] = []
condition_op: str = Query(default="or")
medications: Annotated[list[str], Query()] = []
medication_op: str = Query(default="or")
observations: Annotated[list[str], Query()] = []
observation_op: str = Query(default="or")
```
Pass `conditions=conditions or None` etc. to projector (converts empty list → None).

Same changes to `get_facets` endpoint.

### Step 3 — `frontend/src/api/types.ts`
Replace scalar nullable strings in `SearchFilters`:
```typescript
conditions: string[]
condition_op: 'or' | 'and'
medications: string[]
medication_op: 'or' | 'and'
observations: string[]
observation_op: 'or' | 'and'
```

### Step 4 — `frontend/src/api/index.ts`
Update `buildQuery` to handle arrays via `append()`:
```typescript
if (Array.isArray(v)) {
  for (const item of v) q.append(k, item)
} else {
  q.set(k, String(v))
}
```
Update `searchPatients` and `getPatientFacets` to use new field names.

### Step 5 — `frontend/src/stores/patientSearch.ts`
Update reactive filters init (arrays instead of nulls, add `_op` fields).

Add `toggleArrayFilter` action:
```typescript
function toggleArrayFilter(
  key: 'conditions' | 'medications' | 'observations',
  value: string
) {
  const arr = filters[key]
  const idx = arr.indexOf(value)
  idx === -1 ? arr.push(value) : arr.splice(idx, 1)
  filters.page = 1
  fetchResults()
}
```
Update `clearFilters` to reset arrays and ops. Export `toggleArrayFilter`.

### Step 6 — `frontend/src/components/FacetPanel.vue`
Add emit type:
```typescript
(e: 'toggle-array-filter', key: 'conditions' | 'medications' | 'observations', value: string): void
```

For Diagnosis, Medication, Observation sections:
- Change `@click` to emit `toggle-array-filter` instead of `set-filter`
- Change `:class="{ active: ... }"` to use `.includes(b.key)`
- Add AND/OR pill toggle in section header, visible only when `filters.conditions.length > 1`:

```html
<span v-if="filters.conditions.length > 1" class="op-toggle" @click.stop>
  <button :class="['op-btn', { active: filters.condition_op === 'or' }]"
          @click.stop="emit('set-filter', 'condition_op', 'or')">OR</button>
  <button :class="['op-btn', { active: filters.condition_op === 'and' }]"
          @click.stop="emit('set-filter', 'condition_op', 'and')">AND</button>
</span>
```

Update `hasActiveFilters` and `activeFilterCount` computed props to check arrays.

Add CSS for `.op-toggle` / `.op-btn` pill styles.

### Step 7 — `frontend/src/views/PatientListView.vue`
Add handler and wire to FacetPanel:
```typescript
function onToggleArrayFilter(key: 'conditions' | 'medications' | 'observations', value: string) {
  store.toggleArrayFilter(key, value)
}
```
Add `@toggle-array-filter="onToggleArrayFilter"` to `<FacetPanel>`.

---

## Key Design Decisions
- **OR is default** — most intuitive when first adding a second selection
- **Toggle appears at ≥2 selections** — avoids noise when only one item is selected
- **Obs range uses `observations[0]`** — range on multiple observation types is ambiguous; apply to first selected code only
- **Repeated URL params** (`?conditions=I10&conditions=E11`) — FastAPI handles natively, no custom parsing

## Verification
1. Restart FastAPI server
2. Select 2 conditions in the facet panel → AND/OR toggle appears in the section header
3. With OR: result count ≥ either single selection; with AND: count ≤ either single selection
4. Mix multi-condition with single medication — cross-dimension AND still works
5. `curl "http://localhost:8000/patients/search?conditions=I10&conditions=E11&condition_op=or"` returns patients with either code
6. `curl "http://localhost:8000/patients/search?conditions=I10&conditions=E11&condition_op=and"` returns only patients with both codes (should be a subset)
