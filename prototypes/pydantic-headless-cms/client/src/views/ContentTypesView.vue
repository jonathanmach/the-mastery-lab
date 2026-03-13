<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getContentTypes,
  createContentType,
  updateContentType,
  deleteContentType,
  type ContentTypeSchema,
  type FieldDefinition,
  type FieldType,
} from '../api/client'

const contentTypes = ref<ContentTypeSchema[]>([])
const error = ref('')
const showForm = ref(false)
const editingId = ref<string | null>(null)

const FIELD_TYPES: FieldType[] = [
  'text', 'rich_text', 'number', 'integer', 'boolean', 'date', 'datetime', 'list',
]

const emptyForm = (): ContentTypeSchema => ({
  id: '',
  name: '',
  fields: [],
})

const form = ref<ContentTypeSchema>(emptyForm())

async function load() {
  try {
    contentTypes.value = await getContentTypes()
  } catch (e) {
    error.value = String(e)
  }
}

onMounted(load)

function openCreate() {
  form.value = emptyForm()
  editingId.value = null
  showForm.value = true
  error.value = ''
}

function openEdit(ct: ContentTypeSchema) {
  form.value = JSON.parse(JSON.stringify(ct)) // deep copy
  editingId.value = ct.id
  showForm.value = true
  error.value = ''
}

function cancel() {
  showForm.value = false
  error.value = ''
}

function addField() {
  form.value.fields.push({ name: '', type: 'text', required: true, item_type: null })
}

function removeField(i: number) {
  form.value.fields.splice(i, 1)
}

function onFieldTypeChange(field: FieldDefinition) {
  if (field.type !== 'list') {
    field.item_type = null
  } else if (field.item_type === null) {
    field.item_type = 'text'
  }
}

async function submit() {
  error.value = ''
  try {
    if (editingId.value) {
      await updateContentType(editingId.value, form.value)
    } else {
      await createContentType(form.value)
    }
    showForm.value = false
    await load()
  } catch (e) {
    error.value = String(e)
  }
}

async function remove(id: string) {
  if (!confirm(`Delete content type "${id}"? This cannot be undone.`)) return
  try {
    await deleteContentType(id)
    await load()
  } catch (e) {
    error.value = String(e)
  }
}

</script>

<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h1>Content Types</h1>
      <button class="btn-primary" @click="openCreate">+ New Content Type</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <table v-if="contentTypes.length">
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Fields</th>
          <th style="width:140px">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ct in contentTypes" :key="ct.id">
          <td><code>{{ ct.id }}</code></td>
          <td>{{ ct.name }}</td>
          <td>{{ ct.fields.map(f => f.name).join(', ') || '—' }}</td>
          <td>
            <div class="actions">
              <button class="btn-secondary btn-sm" @click="openEdit(ct)">Edit</button>
              <button class="btn-danger btn-sm" @click="remove(ct.id)">Delete</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else style="color:#888;margin-top:12px;">No content types yet. Create one to get started.</p>

    <!-- Form panel -->
    <div v-if="showForm" class="panel">
      <h2>{{ editingId ? 'Edit Content Type' : 'New Content Type' }}</h2>
      <p v-if="error" class="error">{{ error }}</p>

      <label>ID (slug)</label>
      <input
        v-model="form.id"
        type="text"
        placeholder="e.g. blog-post"
        :disabled="!!editingId"
      />

      <label>Name</label>
      <input v-model="form.name" type="text" placeholder="e.g. Blog Post" />

      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <label style="margin-bottom:0">Fields</label>
        <button class="btn-secondary btn-sm" @click="addField">+ Add Field</button>
      </div>

      <div
        v-for="(field, i) in form.fields"
        :key="i"
        style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;"
      >
        <input
          v-model="field.name"
          type="text"
          placeholder="Field name"
          style="flex:2;margin-bottom:0"
        />
        <select v-model="field.type" style="flex:2;margin-bottom:0" @change="onFieldTypeChange(field)">
          <option v-for="ft in FIELD_TYPES" :key="ft" :value="ft">{{ ft }}</option>
        </select>
        <select v-if="field.type === 'list'" v-model="field.item_type" style="flex:2;margin-bottom:0">
          <option v-for="ft in FIELD_TYPES.filter(t => t !== 'list')" :key="ft" :value="ft">{{ ft }}</option>
        </select>
        <label style="display:flex;align-items:center;gap:4px;white-space:nowrap;margin-bottom:0;font-weight:normal;flex:1">
          <input type="checkbox" v-model="field.required" style="width:auto;margin-bottom:0" />
          Required
        </label>
        <button class="btn-danger btn-sm" @click="removeField(i)" style="white-space:nowrap">✕</button>
      </div>

      <div style="display:flex;gap:8px;margin-top:12px;">
        <button class="btn-primary" @click="submit">Save</button>
        <button class="btn-secondary" @click="cancel">Cancel</button>
      </div>
    </div>
  </div>
</template>
