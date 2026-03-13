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
  return s === '' ? null : s  // covers text, rich_text, image (URL string), date, datetime
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
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h1>Content</h1>
      <button class="btn-primary" :disabled="!contentTypes.length" @click="openCreate">
        + New Entry
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <p v-if="!contentTypes.length" style="color:#888;">
      No content types defined yet.
      <RouterLink to="/content-types">Create one first.</RouterLink>
    </p>

    <table v-else-if="entries.length">
      <thead>
        <tr>
          <th>Type</th>
          <th>Preview</th>
          <th style="width:120px">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="entry in entries" :key="entry.id">
          <td><span class="badge">{{ typeName(entry.content_type_id) }}</span></td>
          <td>
            <span v-for="(val, key) in entry.data" :key="key" style="margin-right:12px;">
              <span style="color:#888;font-size:12px;">{{ key }}:</span>
              <template v-if="isImageField(entry, String(key))">
                <img :src="String(val)" style="height:36px;width:36px;object-fit:cover;border-radius:3px;vertical-align:middle;" />
              </template>
              <template v-else-if="Array.isArray(val)">
                <span v-for="(item, i) in val" :key="i" class="tag">{{ item }}</span>
              </template>
              <template v-else>{{ val }}</template>
            </span>
          </td>
          <td>
            <div class="actions">
              <button class="btn-secondary btn-sm" @click="openEdit(entry)">Edit</button>
              <button class="btn-danger btn-sm" @click="remove(entry.id)">Delete</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else style="color:#888;margin-top:12px;">No entries yet. Create one above.</p>

    <!-- Form panel -->
    <div v-if="showForm" class="panel">
      <h2>{{ editingId ? 'Edit Entry' : 'New Entry' }}</h2>
      <p v-if="error" class="error">{{ error }}</p>

      <label>Content Type</label>
      <select v-model="selectedTypeId" :disabled="!!editingId" @change="onTypeChange">
        <option v-for="ct in contentTypes" :key="ct.id" :value="ct.id">{{ ct.name }}</option>
      </select>

      <template v-if="activeSchema">
        <template v-for="field in activeSchema.fields" :key="field.name">
          <label>
            {{ field.name }}
            <span v-if="!field.required" style="font-weight:normal;color:#888"> (optional)</span>
            <span v-if="field.type === 'list'" style="font-weight:normal;color:#888"> — comma-separated</span>
          </label>

          <!-- image -->
          <div v-if="field.type === 'image'" style="margin-bottom:12px;">
            <input
              type="file"
              accept="image/*"
              style="margin-bottom:6px"
              @change="onImageChange(field.name, $event)"
            />
            <span v-if="uploading[field.name]" style="font-size:12px;color:#888;"> Uploading…</span>
            <div v-if="formData[field.name]" style="margin-top:6px;">
              <img :src="String(formData[field.name])" style="max-height:120px;border-radius:4px;" />
            </div>
          </div>

          <!-- boolean -->
          <div v-else-if="field.type === 'boolean'" style="margin-bottom:12px;">
            <label style="display:flex;align-items:center;gap:6px;font-weight:normal;">
              <input
                type="checkbox"
                :checked="!!formData[field.name]"
                style="width:auto;margin-bottom:0"
                @change="(e) => (formData[field.name] = (e.target as HTMLInputElement).checked)"
              />
              {{ field.name }}
            </label>
          </div>

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
        </template>
      </template>

      <div style="display:flex;gap:8px;margin-top:4px;">
        <button class="btn-primary" :disabled="Object.values(uploading).some(Boolean)" @click="submit">
          Save
        </button>
        <button class="btn-secondary" @click="cancel">Cancel</button>
      </div>
    </div>
  </div>
</template>
