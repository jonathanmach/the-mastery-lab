export interface ContentEntry {
  id: string
  content_type_id: string
  data: Record<string, unknown>
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`)
  return res.json() as Promise<T>
}

export function getBlogPosts(): Promise<ContentEntry[]> {
  return fetchJSON('/public/content-types/blog-post/entries')
}

export function getBlogPost(id: string): Promise<ContentEntry> {
  return fetchJSON(`/public/entries/${id}`)
}
