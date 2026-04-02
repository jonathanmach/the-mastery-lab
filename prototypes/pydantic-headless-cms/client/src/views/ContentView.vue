<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  getAllEntries,
  getContentTypes,
  getContentType,
  createEntry,
  updateEntry,
  deleteEntry,
  uploadFile,
  type ContentTypeSchema,
  type ContentEntry,
  type FieldDefinition,
} from '../api/client'

const entries = ref<ContentEntry[]>([])
const contentTypes = ref<ContentTypeSchema[]>([])
const schemaCache = ref<Record<string, ContentTypeSchema>>({})

const error = ref('')
const showForm = ref(false)
const editingId = ref<string | null>(null)
const selectedTypeId = ref('')
const formData = ref<Record<string, unknown>>({})
const uploading = ref<Record<string, boolean>>({})

async function load() {
  error.value = ''
  try {
    ;[entries.value, contentTypes.value] = await Promise.all([
      getAllEntries(),
      getContentTypes(),
    ])
    for (const ct of contentTypes.value) {
      schemaCache.value[ct.id] = ct
    }
  } catch (e) {
    error.value = String(e)
  }
}

onMounted(load)

async function ensureSchema(typeId: string): Promise<ContentTypeSchema | null> {
  if (!schemaCache.value[typeId]) {
    try {
      schemaCache.value[typeId] = await getContentType(typeId)
    } catch {
      return null
    }
  }
  return schemaCache.value[typeId]
}

function typeName(typeId: string): string {
  return schemaCache.value[typeId]?.name ?? typeId
}

function emptyForm(schema: ContentTypeSchema): Record<string, unknown> {
  return Object.fromEntries(
    schema.fields.map((f) => [f.name, f.type === 'boolean' ? false : '']),
  )
}

function openCreate() {
  selectedTypeId.value = contentTypes.value[0]?.id ?? ''
  if (selectedTypeId.value) {
    formData.value = emptyForm(schemaCache.value[selectedTypeId.value])
  }
  editingId.value = null
  showForm.value = true
  error.value = ''
}

function onTypeChange() {
  const schema = schemaCache.value[selectedTypeId.value]
  if (schema) formData.value = emptyForm(schema)
}

async function openEdit(entry: ContentEntry) {
  const schema = await ensureSchema(entry.content_type_id)
  if (!schema) return
  editingId.value = entry.id
  selectedTypeId.value = entry.content_type_id
  formData.value = Object.fromEntries(
    schema.fields.map((f) => {
      const v = entry.data[f.name]
      if (f.type === 'list' && Array.isArray(v)) return [f.name, v.join(', ')]
      return [f.name, v ?? '']
    }),
  )
  showForm.value = true
  error.value = ''
}

function cancel() {
  showForm.value = false
  error.value = ''
}

async function onImageChange(fieldName: string, e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value[fieldName] = true
  try {
    const { url } = await uploadFile(file)
    formData.value[fieldName] = url
  } catch (err) {
    error.value = String(err)
  } finally {
    uploading.value[fieldName] = false
  }
}

function coerce(field: FieldDefinition, raw: unknown): unknown {
  const s = String(raw ?? '')
  if (field.type === 'boolean') return raw === true || raw === 'true'
  if (field.type === 'integer') return s === '' ? null : parseInt(s, 10)
  if (field.type === 'number') return s === '' ? null : parseFloat(s)
  if (field.type === 'list') return s.split(',').map((x) => x.trim()).filter(Boolean)
  return s === '' ? null : s
}

async function submit() {
  error.value = ''
  const schema = schemaCache.value[selectedTypeId.value]
  if (!schema) return
  const data: Record<string, unknown> = {}
  for (const field of schema.fields) {
    const coerced = coerce(field, formData.value[field.name])
    if (coerced !== null) data[field.name] = coerced
  }
  try {
    if (editingId.value) {
      await updateEntry(editingId.value, data)
    } else {
      await createEntry(selectedTypeId.value, data)
    }
    showForm.value = false
    await load()
  } catch (e) {
    error.value = String(e)
  }
}

async function remove(id: string) {
  if (!confirm('Delete this entry?')) return
  try {
    await deleteEntry(id)
    await load()
  } catch (e) {
    error.value = String(e)
  }
}

function isImageField(entry: ContentEntry, key: string): boolean {
  const schema = schemaCache.value[entry.content_type_id]
  return schema?.fields.find((f) => f.name === key)?.type === 'image'
}

const activeSchema = computed(() => schemaCache.value[selectedTypeId.value] ?? null)
</script>

<template>
  <div>
    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1>Content</h1>
        <p class="page-header-meta">
          {{ entries.length }} entr{{ entries.length !== 1 ? 'ies' : 'y' }}
        </p>
      </div>
      <button
        class="btn btn-primary"
        :disabled="!contentTypes.length"
        @click="openCreate"
      >
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <path d="M6.5 1v11M1 6.5h11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        New Entry
      </button>
    </div>

    <div class="page-body">
      <p v-if="error" class="error-alert">{{ error }}</p>

      <!-- No content types -->
      <div v-if="!contentTypes.length" class="table-wrap">
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <path d="M11 3L3 7v7c0 4.4 3 8.5 8 10 5-1.5 8-5.6 8-10V7L11 3z" stroke="#94a3b8" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3>No content types defined</h3>
          <p>
            <RouterLink to="/content-types" class="link">Create a content type →</RouterLink>
          </p>
        </div>
      </div>

      <template v-else>
        <div class="table-wrap">
          <table v-if="entries.length">
            <thead>
              <tr>
                <th style="width:130px">Type</th>
                <th>Preview</th>
                <th style="width:130px">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in entries" :key="entry.id">
                <td>
                  <span class="badge">{{ typeName(entry.content_type_id) }}</span>
                </td>
                <td>
                  <div class="entry-preview">
                    <div
                      v-for="(val, key) in entry.data"
                      :key="key"
                      class="preview-cell"
                    >
                      <span class="preview-key">{{ key }}</span>
                      <template v-if="isImageField(entry, String(key))">
                        <img :src="String(val)" class="preview-thumb" />
                      </template>
                      <template v-else-if="Array.isArray(val)">
                        <span v-for="(item, i) in val.slice(0, 3)" :key="i" class="tag">{{ item }}</span>
                        <span v-if="val.length > 3" class="overflow-count">+{{ val.length - 3 }}</span>
                      </template>
                      <template v-else>
                        <span class="preview-val">{{ val }}</span>
                      </template>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="actions">
                    <button class="btn btn-secondary btn-sm" @click="openEdit(entry)">Edit</button>
                    <button class="btn btn-danger btn-sm" @click="remove(entry.id)">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-else class="empty-state">
            <div class="empty-state-icon">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <rect x="2" y="2" width="18" height="18" rx="3" stroke="#94a3b8" stroke-width="1.5"/>
                <path d="M7 11h8M7 7h8M7 15h5" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>No entries yet</h3>
            <p>Click <strong>New Entry</strong> to create your first one.</p>
          </div>
        </div>

        <!-- Form panel -->
        <div v-if="showForm" class="form-card">
          <div class="form-card-header">
            <div class="form-card-header-icon">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                <path d="M2 10V8l5-5 2 2-5 5H2zM8.5 3.5l1-1 1 1-1 1-1-1z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
              </svg>
            </div>
            <h2>{{ editingId ? 'Edit Entry' : 'New Entry' }}</h2>
          </div>

          <div class="form-card-body">
            <p v-if="error" class="error-alert">{{ error }}</p>

            <div class="form-group">
              <label class="field-label">Content Type</label>
              <select v-model="selectedTypeId" :disabled="!!editingId" @change="onTypeChange">
                <option v-for="ct in contentTypes" :key="ct.id" :value="ct.id">{{ ct.name }}</option>
              </select>
            </div>

            <template v-if="activeSchema">
              <div class="fields-divider">
                <span>{{ activeSchema.name }} fields</span>
              </div>

              <div v-for="field in activeSchema.fields" :key="field.name" class="form-group">
                <label class="field-label">
                  {{ field.name }}
                  <span v-if="!field.required" class="field-optional"> — optional</span>
                  <span v-if="field.type === 'list'" class="field-hint"> — comma-separated</span>
                </label>

                <!-- image -->
                <div v-if="field.type === 'image'" class="image-field">
                  <label class="file-label">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                      <path d="M2 10l3-3 2 2 3-4 2 5H2z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
                      <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.2"/>
                    </svg>
                    Choose image
                    <input type="file" accept="image/*" class="file-input-hidden" @change="onImageChange(field.name, $event)" />
                  </label>
                  <span v-if="uploading[field.name]" class="uploading-badge">Uploading…</span>
                  <div v-if="formData[field.name]" class="image-preview-wrap">
                    <img :src="String(formData[field.name])" class="image-preview" />
                  </div>
                </div>

                <!-- boolean -->
                <label v-else-if="field.type === 'boolean'" class="toggle-label">
                  <input
                    type="checkbox"
                    :checked="!!formData[field.name]"
                    class="toggle-checkbox"
                    @change="(e) => (formData[field.name] = (e.target as HTMLInputElement).checked)"
                  />
                  <span class="toggle-text">{{ field.name }}</span>
                </label>

                <input
                  v-else-if="field.type === 'integer' || field.type === 'number'"
                  v-model="formData[field.name]"
                  type="number"
                  :step="field.type === 'integer' ? '1' : 'any'"
                />
                <input
                  v-else-if="field.type === 'date'"
                  v-model="formData[field.name]"
                  type="date"
                />
                <input
                  v-else-if="field.type === 'datetime'"
                  v-model="formData[field.name]"
                  type="datetime-local"
                />
                <textarea
                  v-else
                  v-model="(formData[field.name] as string)"
                  :rows="field.type === 'rich_text' ? 6 : 2"
                />
              </div>
            </template>

            <div class="form-actions">
              <button
                class="btn btn-primary"
                :disabled="Object.values(uploading).some(Boolean)"
                @click="submit"
              >
                {{ editingId ? 'Save Changes' : 'Create Entry' }}
              </button>
              <button class="btn btn-secondary" @click="cancel">Cancel</button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.link { color: var(--primary); font-weight: 500; text-decoration: none; }
.link:hover { text-decoration: underline; }

/* Entry preview */
.entry-preview { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.preview-cell { display: flex; align-items: center; gap: 4px; }
.preview-key {
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: 500;
}
.preview-val {
  font-size: 13px;
  color: var(--text);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-thumb {
  height: 30px;
  width: 30px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid var(--border);
}
.overflow-count { font-size: 11px; color: var(--text-tertiary); }

/* Form specifics */
.form-card-header-icon {
  width: 24px; height: 24px;
  border-radius: 6px;
  background: var(--primary-light);
  color: var(--primary-text);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.form-actions { display: flex; gap: 8px; padding-top: 6px; }

.fields-divider {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .05em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}
.fields-divider::before,
.fields-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.field-optional { font-weight: 400; color: var(--text-tertiary); font-style: italic; }
.field-hint { font-weight: 400; color: var(--text-tertiary); font-style: italic; }

/* Image field */
.image-field { display: flex; flex-direction: column; gap: 8px; }
.file-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background .12s, border-color .12s;
  width: fit-content;
}
.file-label:hover { background: var(--surface-raised); border-color: var(--border-hover); color: var(--text); }
.file-input-hidden { display: none; }
.uploading-badge {
  font-size: 12px;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: 5px;
}
.image-preview-wrap { margin-top: 2px; }
.image-preview {
  max-height: 120px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  display: block;
}

/* Boolean */
.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.toggle-checkbox {
  width: 15px !important;
  height: 15px;
  cursor: pointer;
}
.toggle-text { font-size: 13px; color: var(--text-secondary); }
</style>
