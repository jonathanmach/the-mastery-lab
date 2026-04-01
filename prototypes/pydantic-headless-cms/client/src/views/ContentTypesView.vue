<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  getContentTypes,
  listSchemas,
  getSchemaResolved,
  saveSchemaRaw,
  deleteSchema,
  type ContentTypeSchema,
  type FieldDefinition,
  type FieldType,
  type ResolvedSchema,
} from '../api/client'

const contentTypes = ref<ContentTypeSchema[]>([])
const allSchemas = ref<Array<{ id: string; title: string }>>([])
// base map and own-field count built at load time
const baseMap = ref<Record<string, string | null>>({})
const ownFieldCountMap = ref<Record<string, number>>({})

const activeTab = ref<'types' | 'hierarchy'>('types')

const error = ref('')
const showForm = ref(false)
const editingId = ref<string | null>(null)

// ---------------------------------------------------------------------------
// Form state (flat refs instead of one nested object so reactivity is clear)
// ---------------------------------------------------------------------------
const formId   = ref('')
const formName = ref('')
const formBase = ref<string | null>(null)
const formOwnFields       = ref<FieldDefinition[]>([])
const formInheritedFields = ref<FieldDefinition[]>([])

const FIELD_TYPES: FieldType[] = [
  'text', 'rich_text', 'number', 'integer', 'boolean', 'date', 'datetime', 'list', 'image',
]

// ---------------------------------------------------------------------------
// JSON Schema helpers (mirrors server fs_repository._content_type_to_json_schema)
// ---------------------------------------------------------------------------

const PROP_MAP: Partial<Record<FieldType, Record<string, unknown>>> = {
  text:      { type: 'string' },
  rich_text: { type: 'string', 'x-cms-type': 'rich_text' },
  image:     { type: 'string', 'x-cms-type': 'image' },
  number:    { type: 'number' },
  integer:   { type: 'integer' },
  boolean:   { type: 'boolean' },
  date:      { type: 'string', format: 'date' },
  datetime:  { type: 'string', format: 'date-time' },
}

function fieldToProp(f: FieldDefinition): Record<string, unknown> {
  let prop: Record<string, unknown>
  if (f.type === 'list') {
    const itemBase = PROP_MAP[f.item_type ?? 'text'] ?? { type: 'string' }
    prop = { type: 'array', items: { ...itemBase } }
  } else {
    prop = { ...(PROP_MAP[f.type] ?? { type: 'string' }) }
  }
  if (f.label)       prop.title       = f.label
  if (f.description) prop.description = f.description
  return prop
}

function buildRawSchema(
  id: string,
  name: string,
  base: string | null,
  ownFields: FieldDefinition[],
): Record<string, unknown> {
  const properties: Record<string, unknown> = {}
  const required: string[] = []
  for (const f of ownFields) {
    properties[f.name] = fieldToProp(f)
    if (f.required) required.push(f.name)
  }
  const raw: Record<string, unknown> = {
    $schema: 'https://json-schema.org/draft/2020-12/schema',
    $id: id,
    title: name,
    'x-cms': { base },
    type: 'object',
    properties,
  }
  if (required.length) raw.required = required
  return raw
}

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

interface Template { label: string; description: string; icon: string; fields: FieldDefinition[] }

const TEMPLATES: Template[] = [
  {
    label: 'Blog Post', description: 'Title, body, author, tags, cover image', icon: '✍️',
    fields: [
      { name: 'title',        type: 'text',      required: true,  item_type: null, label: null, description: null },
      { name: 'body',         type: 'rich_text', required: true,  item_type: null, label: null, description: null },
      { name: 'author',       type: 'text',      required: true,  item_type: null, label: null, description: null },
      { name: 'published_at', type: 'date',       required: false, item_type: null, label: null, description: null },
      { name: 'tags',         type: 'list',       required: false, item_type: 'text', label: null, description: null },
      { name: 'cover_image',  type: 'image',      required: false, item_type: null, label: null, description: null },
    ],
  },
  {
    label: 'Product', description: 'Name, description, price, SKU, image', icon: '🛍️',
    fields: [
      { name: 'name',        type: 'text',      required: true,  item_type: null, label: null, description: null },
      { name: 'description', type: 'rich_text', required: false, item_type: null, label: null, description: null },
      { name: 'price',       type: 'number',    required: true,  item_type: null, label: null, description: null },
      { name: 'sku',         type: 'text',      required: false, item_type: null, label: null, description: null },
      { name: 'in_stock',    type: 'boolean',   required: true,  item_type: null, label: null, description: null },
      { name: 'image',       type: 'image',     required: false, item_type: null, label: null, description: null },
    ],
  },
  {
    label: 'Team Member', description: 'Name, role, bio, photo', icon: '👤',
    fields: [
      { name: 'name',  type: 'text',      required: true,  item_type: null, label: null, description: null },
      { name: 'role',  type: 'text',      required: true,  item_type: null, label: null, description: null },
      { name: 'bio',   type: 'rich_text', required: false, item_type: null, label: null, description: null },
      { name: 'photo', type: 'image',     required: false, item_type: null, label: null, description: null },
    ],
  },
  {
    label: 'Event', description: 'Title, description, date, location', icon: '📅',
    fields: [
      { name: 'title',       type: 'text',      required: true,  item_type: null, label: null, description: null },
      { name: 'description', type: 'rich_text', required: false, item_type: null, label: null, description: null },
      { name: 'start_date',  type: 'datetime',  required: true,  item_type: null, label: null, description: null },
      { name: 'location',    type: 'text',      required: false, item_type: null, label: null, description: null },
      { name: 'image',       type: 'image',     required: false, item_type: null, label: null, description: null },
    ],
  },
]

// ---------------------------------------------------------------------------
// Load
// ---------------------------------------------------------------------------

async function load() {
  error.value = ''
  try {
    const [cts, schemas] = await Promise.all([getContentTypes(), listSchemas()])
    contentTypes.value = cts
    allSchemas.value = schemas
    // Build base map for table display (parallel, ignore failures)
    const resolved = await Promise.all(
      schemas.map(s => getSchemaResolved(s.id).catch(() => null)),
    )
    baseMap.value = {}
    ownFieldCountMap.value = {}
    for (const r of resolved) {
      if (r) {
        baseMap.value[r.id] = r.base
        ownFieldCountMap.value[r.id] = r.own_fields.length
      }
    }
  } catch (e) {
    error.value = String(e)
  }
}

onMounted(load)

// ---------------------------------------------------------------------------
// Form open/close
// ---------------------------------------------------------------------------

function openCreate() {
  formId.value = ''
  formName.value = ''
  formBase.value = null
  formOwnFields.value = []
  formInheritedFields.value = []
  editingId.value = null
  showForm.value = true
  error.value = ''
}

async function openEdit(ct: ContentTypeSchema) {
  error.value = ''
  try {
    const resolved: ResolvedSchema = await getSchemaResolved(ct.id)
    formId.value   = ct.id
    formName.value = ct.name
    formBase.value = resolved.base
    formOwnFields.value       = JSON.parse(JSON.stringify(resolved.own_fields))
    formInheritedFields.value = resolved.inherited_fields
    editingId.value = ct.id
    showForm.value  = true
  } catch (e) {
    error.value = String(e)
  }
}

function cancel() {
  showForm.value = false
  error.value = ''
}

// ---------------------------------------------------------------------------
// Base change — reload inherited fields from the selected parent
// ---------------------------------------------------------------------------

async function onBaseChange() {
  if (!formBase.value) {
    formInheritedFields.value = []
    return
  }
  try {
    const parent = await getSchemaResolved(formBase.value)
    // Show ALL parent fields (its inherited + its own) as inherited in this schema
    formInheritedFields.value = [...parent.inherited_fields, ...parent.own_fields]
  } catch (e) {
    error.value = String(e)
    formInheritedFields.value = []
  }
}

// ---------------------------------------------------------------------------
// Field builder (own fields only)
// ---------------------------------------------------------------------------

function addField() {
  formOwnFields.value.push({
    name: '', type: 'text', required: true, item_type: null, label: null, description: null,
  })
}

function removeField(i: number) {
  formOwnFields.value.splice(i, 1)
}

function onFieldTypeChange(field: FieldDefinition) {
  if (field.type !== 'list') field.item_type = null
  else if (field.item_type === null) field.item_type = 'text'
}

function applyTemplate(t: Template) {
  formOwnFields.value = JSON.parse(JSON.stringify(t.fields))
  // Templates don't set ID/name — let the user fill those, but pre-fill as hint
}

// ---------------------------------------------------------------------------
// Save / Delete
// ---------------------------------------------------------------------------

async function submit() {
  error.value = ''
  if (!formId.value.trim()) { error.value = 'ID is required.'; return }
  if (!formName.value.trim()) { error.value = 'Name is required.'; return }
  try {
    const raw = buildRawSchema(formId.value, formName.value, formBase.value, formOwnFields.value)
    await saveSchemaRaw(formId.value, raw)
    showForm.value = false
    await load()
  } catch (e) {
    error.value = String(e)
  }
}

async function remove(id: string) {
  if (!confirm(`Delete content type "${id}"? This cannot be undone.`)) return
  try {
    await deleteSchema(id)
    await load()
  } catch (e) {
    error.value = String(e)
  }
}

// ---------------------------------------------------------------------------
// Computed helpers
// ---------------------------------------------------------------------------

// Schemas available as base options: everything except the schema being edited
const baseOptions = computed(() =>
  allSchemas.value.filter(s => s.id !== editingId.value),
)

function baseName(id: string | null): string | null {
  if (!id) return null
  return allSchemas.value.find(s => s.id === id)?.title ?? id
}

// ---------------------------------------------------------------------------
// Hierarchy / tree
// ---------------------------------------------------------------------------

interface TreeNode {
  id: string
  name: string
  base: string | null
  totalFields: number
  ownFields: number
  children: TreeNode[]
}

interface TreeRow {
  id: string
  name: string
  base: string | null
  totalFields: number
  ownFields: number
  depth: number
  isLast: boolean
  hasChildren: boolean
  /** true at index k = draw a vertical continuation line at ancestor depth k */
  ancestorLines: boolean[]
}

function flattenTree(nodes: TreeNode[], depth: number, lines: boolean[]): TreeRow[] {
  const rows: TreeRow[] = []
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i]
    const isLast = i === nodes.length - 1
    rows.push({
      id: node.id, name: node.name, base: node.base,
      totalFields: node.totalFields, ownFields: node.ownFields,
      depth, isLast, hasChildren: node.children.length > 0,
      ancestorLines: [...lines],
    })
    if (node.children.length > 0) {
      rows.push(...flattenTree(node.children, depth + 1, [...lines, !isLast]))
    }
  }
  return rows
}

const treeData = computed<TreeNode[]>(() => {
  const nodes: Record<string, TreeNode> = {}
  for (const ct of contentTypes.value) {
    nodes[ct.id] = {
      id: ct.id, name: ct.name,
      base: baseMap.value[ct.id] ?? null,
      totalFields: ct.fields.length,
      ownFields: ownFieldCountMap.value[ct.id] ?? ct.fields.length,
      children: [],
    }
  }
  const roots: TreeNode[] = []
  for (const node of Object.values(nodes)) {
    if (node.base && nodes[node.base]) nodes[node.base].children.push(node)
    else roots.push(node)
  }
  // Sort each level: parents with children first
  function sort(ns: TreeNode[]) {
    ns.sort((a, b) => b.children.length - a.children.length || a.name.localeCompare(b.name))
    ns.forEach(n => sort(n.children))
  }
  sort(roots)
  return roots
})

const treeRows = computed(() => flattenTree(treeData.value, 0, []))

const treeStats = computed(() => ({
  total: contentTypes.value.length,
  roots: treeData.value.length,
  inherited: treeRows.value.filter(r => r.base !== null).length,
}))

function openEditById(id: string) {
  const ct = contentTypes.value.find(c => c.id === id)
  if (ct) openEdit(ct)
}
</script>

<template>
  <div>
    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1>Content Types</h1>
        <p class="page-header-meta">
          {{ contentTypes.length }} type{{ contentTypes.length !== 1 ? 's' : '' }} defined
        </p>
      </div>
      <div class="header-right">
        <div class="tab-group">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'types' }"
            @click="activeTab = 'types'"
          >
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
              <rect x="1" y="1" width="11" height="11" rx="2" stroke="currentColor" stroke-width="1.4"/>
              <path d="M3.5 4.5h6M3.5 6.5h6M3.5 8.5h4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
            Types
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'hierarchy' }"
            @click="activeTab = 'hierarchy'"
          >
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
              <circle cx="6.5" cy="2" r="1.5" stroke="currentColor" stroke-width="1.2"/>
              <circle cx="2" cy="10" r="1.5" stroke="currentColor" stroke-width="1.2"/>
              <circle cx="11" cy="10" r="1.5" stroke="currentColor" stroke-width="1.2"/>
              <path d="M6.5 3.5v2.5H2v2.5M6.5 6H11v2.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Hierarchy
          </button>
        </div>
        <button v-if="activeTab === 'types'" class="btn btn-primary" @click="openCreate">
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
            <path d="M6.5 1v11M1 6.5h11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          New Content Type
        </button>
      </div>
    </div>

    <div class="page-body">
      <p v-if="error" class="error-alert">{{ error }}</p>

      <!-- ── Hierarchy tab ───────────────────────────────── -->
      <template v-if="activeTab === 'hierarchy'">
        <!-- Stats strip -->
        <div class="tree-stats-bar">
          <div class="tree-stat">
            <span class="tree-stat-value">{{ treeStats.total }}</span>
            <span class="tree-stat-label">total</span>
          </div>
          <div class="tree-stat-divider"></div>
          <div class="tree-stat">
            <span class="tree-stat-value">{{ treeStats.roots }}</span>
            <span class="tree-stat-label">root{{ treeStats.roots !== 1 ? 's' : '' }}</span>
          </div>
          <div class="tree-stat-divider"></div>
          <div class="tree-stat">
            <span class="tree-stat-value">{{ treeStats.inherited }}</span>
            <span class="tree-stat-label">extended</span>
          </div>
        </div>

        <div class="table-wrap tree-wrap">
          <div v-if="!treeRows.length" class="empty-state">
            <div class="empty-state-icon">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <circle cx="11" cy="4" r="2.5" stroke="#94a3b8" stroke-width="1.5"/>
                <circle cx="4"  cy="17" r="2.5" stroke="#94a3b8" stroke-width="1.5"/>
                <circle cx="18" cy="17" r="2.5" stroke="#94a3b8" stroke-width="1.5"/>
                <path d="M11 6.5v4H4v4M11 10.5H18v4" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>No schemas yet</h3>
            <p>Create a content type to see its hierarchy here.</p>
          </div>

          <div v-else class="tree-list">
            <div
              v-for="row in treeRows"
              :key="row.id"
              class="tree-row"
              @click="openEditById(row.id)"
            >
              <!-- Connector lines -->
              <div class="tree-indent">
                <div
                  v-for="(showLine, ai) in row.ancestorLines"
                  :key="ai"
                  class="tree-indent-unit"
                >
                  <div v-if="showLine" class="tree-vline"></div>
                </div>
                <div
                  v-if="row.depth > 0"
                  class="tree-connector"
                  :class="{ last: row.isLast }"
                ></div>
              </div>

              <!-- Node -->
              <div class="tree-node" :class="{ 'is-root': row.depth === 0, 'has-children': row.hasChildren }">
                <div class="tree-node-icon">
                  <!-- branch icon if has children, leaf if not -->
                  <svg v-if="row.hasChildren" width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <rect x="1" y="1" width="11" height="11" rx="2" fill="var(--primary-light)" stroke="var(--primary)" stroke-width="1.2"/>
                    <path d="M4 4h5M4 6.5h5M4 9h3" stroke="var(--primary-text)" stroke-width="1.1" stroke-linecap="round"/>
                  </svg>
                  <svg v-else width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <rect x="1" y="1" width="11" height="11" rx="2" stroke="var(--border-hover)" stroke-width="1.2"/>
                    <path d="M4 4h5M4 6.5h5M4 9h3" stroke="var(--text-tertiary)" stroke-width="1.1" stroke-linecap="round"/>
                  </svg>
                </div>

                <div class="tree-node-info">
                  <span class="tree-node-name">{{ row.name }}</span>
                  <code class="tree-node-id">{{ row.id }}</code>
                </div>

                <div class="tree-node-fields">
                  <span class="tree-field-pill">
                    {{ row.ownFields }} own
                  </span>
                  <span v-if="row.totalFields > row.ownFields" class="tree-field-pill inherited-pill">
                    +{{ row.totalFields - row.ownFields }} inherited
                  </span>
                </div>

                <div class="tree-node-actions" @click.stop>
                  <button class="btn btn-secondary btn-sm" @click="openEditById(row.id)">Edit</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ── Types tab ───────────────────────────────────── -->
      <template v-if="activeTab === 'types'">

      <!-- Table -->
      <div class="table-wrap">
        <table v-if="contentTypes.length">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Extends</th>
              <th>Fields</th>
              <th style="width:150px">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ct in contentTypes" :key="ct.id">
              <td><code>{{ ct.id }}</code></td>
              <td style="color:var(--text);font-weight:500;">{{ ct.name }}</td>
              <td>
                <span v-if="baseMap[ct.id]" class="base-badge">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                    <path d="M5 1v6M2 4l3-3 3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M1 9h8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                  </svg>
                  {{ baseName(baseMap[ct.id]) }}
                </span>
                <span v-else style="color:var(--text-tertiary);">—</span>
              </td>
              <td>
                <div v-if="ct.fields.length" class="field-tags">
                  <span v-for="f in ct.fields.slice(0, 4)" :key="f.name" class="tag">{{ f.name }}</span>
                  <span v-if="ct.fields.length > 4" class="overflow-count">+{{ ct.fields.length - 4 }}</span>
                </div>
                <span v-else style="color:var(--text-tertiary);">—</span>
              </td>
              <td>
                <div class="actions">
                  <button class="btn btn-secondary btn-sm" @click="openEdit(ct)">Edit</button>
                  <button class="btn btn-danger btn-sm" @click="remove(ct.id)">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="empty-state">
          <div class="empty-state-icon">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <rect x="2" y="2" width="18" height="18" rx="3" stroke="#94a3b8" stroke-width="1.5"/>
              <path d="M6 8h10M6 11h10M6 14h6" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <h3>No content types yet</h3>
          <p>Create your first schema to start managing content.</p>
        </div>
      </div>

      <!-- ── Form panel ──────────────────────────────────── -->
      <div v-if="showForm" class="form-card">
        <div class="form-card-header">
          <div class="form-card-header-icon">
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
              <rect x="1" y="1" width="11" height="11" rx="2" stroke="currentColor" stroke-width="1.5"/>
              <path d="M4 4.5h5M4 6.5h5M4 8.5h3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </div>
          <h2>{{ editingId ? 'Edit Content Type' : 'New Content Type' }}</h2>
        </div>

        <div class="form-card-body">
          <p v-if="error" class="error-alert">{{ error }}</p>

          <!-- Templates (create only) -->
          <template v-if="!editingId">
            <p class="section-label">Start from a template</p>
            <div class="templates-grid">
              <button
                v-for="t in TEMPLATES"
                :key="t.label"
                class="template-card"
                @click="applyTemplate(t)"
              >
                <span class="template-icon">{{ t.icon }}</span>
                <div class="template-label">{{ t.label }}</div>
                <div class="template-desc">{{ t.description }}</div>
              </button>
            </div>
            <div class="divider"></div>
          </template>

          <!-- ID + Name -->
          <div class="two-col">
            <div class="form-group">
              <label class="field-label">ID (slug)</label>
              <input
                v-model="formId"
                type="text"
                placeholder="e.g. blog-post"
                :disabled="!!editingId"
              />
            </div>
            <div class="form-group">
              <label class="field-label">Name</label>
              <input v-model="formName" type="text" placeholder="e.g. Blog Post" />
            </div>
          </div>

          <!-- Extends -->
          <div class="form-group">
            <label class="field-label">Extends</label>
            <div class="extends-row">
              <select v-model="formBase" class="extends-select" @change="onBaseChange">
                <option :value="null">— None —</option>
                <option v-for="s in baseOptions" :key="s.id" :value="s.id">
                  {{ s.title }} ({{ s.id }})
                </option>
              </select>
              <span v-if="formBase" class="extends-hint">
                Inherited fields are read-only and cannot be modified here.
              </span>
            </div>
          </div>

          <!-- Inherited fields (read-only) -->
          <template v-if="formInheritedFields.length">
            <div class="section-header inherited-header">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 1v7M3 5l3-3 3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M1 11h10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
              </svg>
              Inherited from <strong>{{ baseName(formBase) }}</strong>
              <span class="field-count-pill">{{ formInheritedFields.length }}</span>
            </div>

            <div class="fields-list inherited-list">
              <div
                v-for="field in formInheritedFields"
                :key="field.name"
                class="field-row inherited-row"
              >
                <div class="field-row-main">
                  <svg class="lock-icon" width="11" height="11" viewBox="0 0 11 11" fill="none">
                    <rect x="1.5" y="4.5" width="8" height="6" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
                    <path d="M3.5 4.5V3a2 2 0 014 0v1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                  </svg>
                  <input :value="field.name"  type="text" disabled class="field-name-input" />
                  <select :value="field.type" disabled class="field-type-select">
                    <option :value="field.type">{{ field.type }}</option>
                  </select>
                  <select v-if="field.type === 'list'" :value="field.item_type" disabled class="field-item-select">
                    <option :value="field.item_type">{{ field.item_type }}</option>
                  </select>
                  <label class="required-check muted">
                    <input type="checkbox" :checked="field.required" disabled />
                    <span>Required</span>
                  </label>
                </div>
                <div v-if="field.label" class="field-row-meta">
                  <input :value="field.label" type="text" disabled class="field-label-input" />
                </div>
              </div>
            </div>
          </template>

          <!-- Own fields -->
          <div class="form-group">
            <div class="section-header own-header">
              <span>
                Own Fields
                <span class="field-count-pill">{{ formOwnFields.length }}</span>
              </span>
              <button class="btn btn-secondary btn-sm" @click="addField">
                <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                  <path d="M5.5 1v9M1 5.5h9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                </svg>
                Add Field
              </button>
            </div>

            <div v-if="formOwnFields.length" class="fields-list">
              <div
                v-for="(field, i) in formOwnFields"
                :key="i"
                class="field-row"
              >
                <div class="field-row-main">
                  <span class="field-row-num">{{ i + 1 }}</span>
                  <input
                    v-model="field.name"
                    type="text"
                    placeholder="field_name"
                    class="field-name-input"
                  />
                  <select
                    v-model="field.type"
                    class="field-type-select"
                    @change="onFieldTypeChange(field)"
                  >
                    <option v-for="ft in FIELD_TYPES" :key="ft" :value="ft">{{ ft }}</option>
                  </select>
                  <select
                    v-if="field.type === 'list'"
                    v-model="field.item_type"
                    class="field-item-select"
                  >
                    <option
                      v-for="ft in FIELD_TYPES.filter(t => t !== 'list')"
                      :key="ft"
                      :value="ft"
                    >{{ ft }}</option>
                  </select>
                  <label class="required-check">
                    <input type="checkbox" v-model="field.required" />
                    <span>Required</span>
                  </label>
                  <button class="remove-btn" title="Remove" @click="removeField(i)">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                    </svg>
                  </button>
                </div>
                <div class="field-row-meta">
                  <input
                    :value="field.label ?? ''"
                    type="text"
                    placeholder="Title (optional display label)"
                    class="field-label-input"
                    @input="field.label = ($event.target as HTMLInputElement).value || null"
                  />
                </div>
              </div>
            </div>

            <div v-else class="fields-empty">
              No own fields yet — click <strong>Add Field</strong> to begin.
            </div>
          </div>

          <div class="form-actions">
            <button class="btn btn-primary" @click="submit">
              {{ editingId ? 'Save Changes' : 'Create Content Type' }}
            </button>
            <button class="btn btn-secondary" @click="cancel">Cancel</button>
          </div>
        </div>
      </div>

      </template><!-- end types tab -->
    </div>
  </div>
</template>

<style scoped>
.field-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.overflow-count { font-size: 11px; color: var(--text-tertiary); align-self: center; padding-left: 2px; }

/* Base badge in table */
.base-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  font-weight: 500;
  color: var(--primary-text);
  background: var(--primary-light);
  border-radius: 20px;
  padding: 2px 8px;
}

/* Extends row */
.extends-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.extends-select { flex: 1; min-width: 200px; }
.extends-hint {
  font-size: 11.5px;
  color: var(--text-tertiary);
  font-style: italic;
}

/* Section headers */
.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  margin-bottom: 8px;
}
.inherited-header {
  color: var(--text-tertiary);
  margin-top: 4px;
}
.own-header {
  color: var(--text-secondary);
  justify-content: space-between;
}
.own-header > span { display: flex; align-items: center; gap: 6px; }
.field-count-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--surface-subtle);
  color: var(--text-tertiary);
  font-size: 10px;
  font-weight: 700;
}

/* Fields list */
.fields-list {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 14px;
}
.inherited-list {
  border-style: dashed;
  opacity: .75;
}
.field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.field-row:last-child { border-bottom: none; }
.field-row:nth-child(even) { background: var(--surface-raised); }

.inherited-row { cursor: not-allowed; }

.field-row-main { display: flex; align-items: center; gap: 8px; }
.field-row-meta { display: flex; padding-left: 26px; }

.lock-icon { flex-shrink: 0; color: var(--text-tertiary); }

.field-name-input  { flex: 2.5; min-width: 0; padding: 5px 8px; font-size: 12px; }
.field-type-select { flex: 2; min-width: 0; padding: 5px 8px; font-size: 12px; }
.field-item-select { flex: 2; min-width: 0; padding: 5px 8px; font-size: 12px; }

.field-label-input {
  flex: 1;
  padding: 4px 8px !important;
  font-size: 11.5px !important;
  color: var(--text-tertiary) !important;
  border-style: dashed !important;
}
.field-label-input:focus {
  border-style: solid !important;
  color: var(--text) !important;
}

.required-check {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  flex-shrink: 0;
  cursor: pointer;
}
.required-check.muted { cursor: not-allowed; color: var(--text-tertiary); }
.required-check input[type=checkbox] { width: auto; margin: 0; cursor: pointer; }
.required-check.muted input { cursor: not-allowed; }

.field-row-num {
  width: 18px; height: 18px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 4px;
  background: var(--surface-subtle);
  color: var(--text-tertiary);
  font-size: 10px; font-weight: 600;
  flex-shrink: 0;
}
.remove-btn {
  width: 26px; height: 26px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px;
  background: transparent;
  color: var(--text-tertiary);
  border: none; cursor: pointer; flex-shrink: 0;
  transition: background .12s, color .12s;
}
.remove-btn:hover { background: var(--danger-light); color: var(--danger); }

.fields-empty {
  border: 1.5px dashed var(--border);
  border-radius: var(--radius);
  padding: 20px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  margin-bottom: 14px;
}

/* Templates */
.section-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 10px; }
.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}
.template-card {
  text-align: left; padding: 10px 12px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); cursor: pointer; font-family: inherit;
  transition: border-color .12s, background .12s, box-shadow .12s;
}
.template-card:hover {
  border-color: var(--primary); background: var(--primary-light);
  box-shadow: 0 0 0 3px rgb(79 70 229 / .08);
}
.template-icon { font-size: 18px; display: block; margin-bottom: 6px; }
.template-label { font-size: 13px; font-weight: 600; color: var(--text); }
.template-desc { font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }

/* Layout helpers */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-card-header-icon {
  width: 24px; height: 24px; border-radius: 6px;
  background: var(--primary-light); color: var(--primary-text);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.form-actions { display: flex; gap: 8px; padding-top: 6px; }

/* ── Tab group (in page header) ──────────────────────────── */
.header-right { display: flex; align-items: center; gap: 10px; }
.tab-group {
  display: flex;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 2px;
  gap: 2px;
}
.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 11px;
  border-radius: calc(var(--radius) - 2px);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background .12s, color .12s;
}
.tab-btn:hover { color: var(--text-secondary); background: var(--surface-raised); }
.tab-btn.active {
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow-sm);
}

/* ── Hierarchy stats bar ────────────────────────────────── */
.tree-stats-bar {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 14px;
  box-shadow: var(--shadow-sm);
}
.tree-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 20px;
  gap: 2px;
}
.tree-stat-value { font-size: 22px; font-weight: 700; color: var(--text); line-height: 1; }
.tree-stat-label { font-size: 11px; font-weight: 500; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: .05em; }
.tree-stat-divider { width: 1px; height: 36px; background: var(--border); flex-shrink: 0; }

/* ── Tree container ─────────────────────────────────────── */
.tree-wrap { overflow: visible; }
.tree-list { padding: 8px 0; }

.tree-row {
  display: flex;
  align-items: stretch;
  min-height: 52px;
  cursor: pointer;
  transition: background .1s;
}
.tree-row:hover { background: var(--surface-raised); }
.tree-row:hover .tree-node-actions { opacity: 1; }

/* Connector lines */
.tree-indent {
  display: flex;
  flex-shrink: 0;
  padding-left: 16px;
}
.tree-indent-unit {
  width: 24px;
  flex-shrink: 0;
  position: relative;
}
.tree-vline {
  position: absolute;
  left: 12px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--border);
}
.tree-connector {
  width: 24px;
  flex-shrink: 0;
  position: relative;
}
/* Vertical line: top to bottom (non-last) or top to midpoint (last) */
.tree-connector::before {
  content: '';
  position: absolute;
  left: 11px;
  width: 1px;
  background: var(--border);
  top: 0;
}
.tree-connector:not(.last)::before { bottom: 0; }
.tree-connector.last::before       { bottom: 50%; }
/* Horizontal elbow */
.tree-connector::after {
  content: '';
  position: absolute;
  left: 11px;
  right: 0;
  top: 50%;
  height: 1px;
  background: var(--border);
}

/* Node card */
.tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px 10px 8px;
  min-width: 0;
}
.tree-node-icon { flex-shrink: 0; display: flex; align-items: center; }
.tree-node-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}
.tree-node-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
}
.tree-node-id {
  font-family: 'SF Mono', 'Cascadia Code', 'Monaco', monospace;
  font-size: 11px;
  color: var(--text-tertiary);
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 5px;
}
.tree-node-fields { display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
.tree-field-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  background: var(--surface-subtle);
  color: var(--text-tertiary);
  border: 1px solid var(--border);
  white-space: nowrap;
}
.inherited-pill {
  background: var(--primary-light);
  color: var(--primary-text);
  border-color: transparent;
}
.tree-node-actions {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity .12s;
}
</style>
