const BASE = 'http://localhost:8004/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FieldType =
  | 'text'
  | 'rich_text'
  | 'number'
  | 'integer'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'list'
  | 'image'
  | 'ref'

export interface FieldDefinition {
  name: string
  type: FieldType
  required: boolean
  item_type: FieldType | null
  label: string | null        // from JSON Schema "title"
  description: string | null  // from JSON Schema "description"
  ref_schema: string | null      // for type === 'ref'
  item_ref_schema: string | null    // for type === 'list' with item_type === 'ref' (single)
  item_ref_schemas: string[] | null // for type === 'list' with item_type === 'ref' (anyOf)
}

/** Flat ContentTypeSchema — own + inherited fields merged (for Pydantic validation). */
export interface ContentTypeSchema {
  id: string
  name: string
  fields: FieldDefinition[]
}

/**
 * Resolved schema returned by GET /api/schemas/{id}/resolved.
 * Separates own fields from inherited fields for the field-builder UI.
 */
export interface ResolvedSchema {
  id: string
  name: string
  base: string | null
  own_fields: FieldDefinition[]
  inherited_fields: FieldDefinition[]  // read-only in the schema editor
}

export interface ContentEntry {
  id: string
  content_type_id: string
  data: Record<string, unknown>
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// JSON Schema endpoints
// ---------------------------------------------------------------------------

export const listSchemas = () =>
  request<Array<{ id: string; title: string }>>('/schemas')

export const getSchemaRaw = (id: string) =>
  request<Record<string, unknown>>(`/schemas/${id}/raw`)

export const getSchemaResolved = (id: string) =>
  request<ResolvedSchema>(`/schemas/${id}/resolved`)

export const saveSchemaRaw = (id: string, raw: Record<string, unknown>) =>
  request<{ id: string; status: string }>(`/schemas/${id}`, {
    method: 'PUT',
    body: JSON.stringify(raw),
  })

export const deleteSchema = (id: string) =>
  request<void>(`/schemas/${id}`, { method: 'DELETE' })

// ---------------------------------------------------------------------------
// Content Types (field-builder API)
// ---------------------------------------------------------------------------

export const getContentTypes = () =>
  request<ContentTypeSchema[]>('/content-types')

export const getContentType = (id: string) =>
  request<ContentTypeSchema>(`/content-types/${id}`)

export const createContentType = (schema: ContentTypeSchema) =>
  request<ContentTypeSchema>('/content-types', {
    method: 'POST',
    body: JSON.stringify(schema),
  })

export const updateContentType = (id: string, schema: ContentTypeSchema) =>
  request<ContentTypeSchema>(`/content-types/${id}`, {
    method: 'PUT',
    body: JSON.stringify(schema),
  })

export const deleteContentType = (id: string) =>
  request<void>(`/content-types/${id}`, { method: 'DELETE' })

// ---------------------------------------------------------------------------
// Object Storage
// ---------------------------------------------------------------------------

export const uploadFile = async (file: File): Promise<{ key: string; url: string }> => {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Content Entries
// ---------------------------------------------------------------------------

export const getAllEntries = () => request<ContentEntry[]>('/entries')

export const getEntries = (typeId: string) =>
  request<ContentEntry[]>(`/content-types/${typeId}/entries`)

export const createEntry = (typeId: string, data: Record<string, unknown>) =>
  request<ContentEntry>(`/content-types/${typeId}/entries`, {
    method: 'POST',
    body: JSON.stringify({ data }),
  })

export const getEntry = (id: string) => request<ContentEntry>(`/entries/${id}`)

export const updateEntry = (id: string, data: Record<string, unknown>) =>
  request<ContentEntry>(`/entries/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ data }),
  })

export const deleteEntry = (id: string) =>
  request<void>(`/entries/${id}`, { method: 'DELETE' })
