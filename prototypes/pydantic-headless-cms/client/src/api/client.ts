const BASE = 'http://localhost:8004/api'

// ---------------------------------------------------------------------------
// Types (mirrors server-side Pydantic models)
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

export interface FieldDefinition {
  name: string
  type: FieldType
  required: boolean
  item_type: FieldType | null
}

export interface ContentTypeSchema {
  id: string
  name: string
  fields: FieldDefinition[]
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
// Content Types
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
