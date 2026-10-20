<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

interface Column {
  type: string
  name: string
  key?: string
  note?: string
}

interface Entity {
  name: string
  columns: Column[]
  x: number
  y: number
}

interface Relationship {
  from: string
  to: string
  fromCardinality: string
  toCardinality: string
  label: string
}

interface EntityGroup {
  name: string
  entityNames: string[]
}

interface DiagramBounds {
  left: number
  top: number
  width: number
  height: number
}

interface Diagram {
  entities: Entity[]
  relationships: Relationship[]
  groups: EntityGroup[]
}

interface DragState {
  entities: Entity[]
  positions: Array<{ entity: Entity; x: number; y: number }>
  pointerX: number
  pointerY: number
}

interface PanState {
  pointerX: number
  pointerY: number
  scrollLeft: number
  scrollTop: number
}

type ThemeMode = 'system' | 'light' | 'dark'
type ResolvedTheme = Exclude<ThemeMode, 'system'>

const initialSource = `erDiagram
    %% @relate-group Projects & workflow: project, workflow_state, tag
    %% @relate-group Tasks & collaboration: task, task_relation, task_tag, comment, agent_run
    %% @relate-group Conversations: chat, chat_message
    %% @relate-group Terminal sessions: tmux_session

    agent_run {
        integer id PK
        integer task_id FK
        RunnerKind runner
        string model "nullable"
        string effort "nullable"
        RunKind kind
        RunMode mode
        WorkspaceMode workspace_mode
        RunStatus status
        string temporal_workflow_id "nullable"
        string temporal_run_id "nullable"
        string worktree_path "nullable"
        string branch_name "nullable"
        string base_branch "nullable"
        text prompt
        text instruction "nullable"
        text result_summary "nullable"
        text diff "nullable"
        integer exit_code "nullable"
        text error "nullable"
        boolean has_log
        integer input_tokens "nullable"
        integer output_tokens "nullable"
        float cost_usd "nullable"
        datetime created_at
        datetime started_at "nullable"
        datetime finished_at "nullable"
        datetime merged_at "nullable"
        string pr_url "nullable"
    }
    chat {
        integer id PK
        string title
        RunnerKind runner
        string runner_session_id "nullable"
        integer project_id FK "nullable"
        integer task_id FK "nullable"
        datetime archived_at "nullable"
        datetime created_at
        datetime updated_at
    }
    chat_message {
        integer id PK
        integer chat_id FK
        ChatRole role
        text body_md
        integer input_tokens "nullable"
        integer output_tokens "nullable"
        float cost_usd "nullable"
        text error "nullable"
        datetime created_at
    }
    comment {
        integer id PK
        integer task_id FK
        AuthorKind author_kind
        text body_md
        datetime created_at
    }
    project {
        integer id PK
        string title
        text description_md
        boolean is_favorite
        float sort_order
        string repo_path "nullable"
        integer agent_success_status_id FK "nullable"
        datetime created_at
        datetime updated_at
    }
    tag {
        integer id PK
        string name
        string color
        text description_md
        text inject_context "nullable"
        datetime created_at
        datetime updated_at
    }
    task {
        integer id PK
        integer project_id FK
        string title
        text description_md
        text plan_md "nullable"
        integer status_id FK
        Priority priority
        RunMode run_mode
        datetime created_at
        datetime updated_at
        datetime started_at "nullable"
        datetime completed_at "nullable"
    }
    task_relation {
        integer task_id PK, FK
        integer related_id PK, FK
        datetime created_at
    }
    task_tag {
        integer task_id PK, FK
        integer tag_id PK, FK
    }
    tmux_session {
        integer id PK
        integer project_id FK "nullable"
        integer task_id FK "nullable"
        string name
        string label
        string cwd_host
        RunnerKind runner "nullable"
        text initial_command "nullable"
        TmuxSessionStatus status
        datetime created_at
        datetime last_attached_at "nullable"
        datetime terminated_at "nullable"
    }
    workflow_state {
        integer id PK
        integer project_id FK
        string name
        StatusCategory category
        string color
        integer position
    }

    task ||--o{ agent_run : "task_id (CASCADE)"
    project o|--o{ chat : "project_id (CASCADE)"
    task o|--o{ chat : "task_id (CASCADE)"
    chat ||--o{ chat_message : "chat_id (CASCADE)"
    task ||--o{ comment : "task_id (CASCADE)"
    workflow_state o|--o{ project : "agent_success_status_id (SET NULL)"
    project ||--o{ task : "project_id (CASCADE)"
    workflow_state ||--o{ task : "status_id"
    task ||--o{ task_relation : "task_id (CASCADE)"
    task ||--o{ task_relation : "related_id (CASCADE)"
    task ||--o{ task_tag : "task_id (CASCADE)"
    tag ||--o{ task_tag : "tag_id (CASCADE)"
    project o|--o{ tmux_session : "project_id (CASCADE)"
    task o|--o{ tmux_session : "task_id (CASCADE)"
    project ||--o{ workflow_state : "project_id (CASCADE)"`

const canvasScroll = ref<HTMLElement>()
const canvasViewportSize = ref({ width: 0, height: 0 })
let resizeObserver: ResizeObserver | undefined
const canvasAnchor = ref<DiagramBounds>()
const draftSource = ref(initialSource)
const diagram = ref<Diagram>({ entities: [], relationships: [], groups: [] })
const parseError = ref('')
const sourceOpen = ref(localStorage.getItem('relate-source-open') !== 'false')
const zoom = ref(1)
const drag = ref<DragState>()
const handMode = ref(false)
const pan = ref<PanState>()
const savedTheme = localStorage.getItem('relate-theme')
const themeMode = ref<ThemeMode>(
  savedTheme === 'light' || savedTheme === 'dark' ? savedTheme : 'system',
)
const systemColorScheme = window.matchMedia('(prefers-color-scheme: dark)')
const systemTheme = ref<ResolvedTheme>(systemColorScheme.matches ? 'dark' : 'light')
const activeTheme = computed<ResolvedTheme>(() =>
  themeMode.value === 'system' ? systemTheme.value : themeMode.value,
)

const nodeWidth = 248
const headerHeight = 43
const rowHeight = 27
const nodePadding = 36
const minimumCanvasWidth = 1820
const minimumCanvasHeight = 1120
const canvasMargin = 360
const minimumZoom = 0.25
const maximumZoom = 1.5
const canvasWidth = computed(() =>
  Math.max(
    minimumCanvasWidth,
    ...diagram.value.entities.map((entity) => entity.x + nodeWidth + 60),
    ...groupFrames.value.map((group) => group.x + group.width + 60),
  ),
)
const canvasHeight = computed(() =>
  Math.max(
    minimumCanvasHeight,
    ...diagram.value.entities.map((entity) => entity.y + nodeHeight(entity) + 60),
    ...groupFrames.value.map((group) => group.y + group.height + 60),
  ),
)
const editorLineCount = computed(() => draftSource.value.split('\n').length)
const entityCount = computed(() => diagram.value.entities.length)
const relationshipCount = computed(() => diagram.value.relationships.length)
const groupCount = computed(() => diagram.value.groups.length)
const renderedRelationships = computed(() =>
  diagram.value.relationships.flatMap((relation, index) => {
    const path = relationPath(relation)
    return path ? [{ relation, path, key: `${relation.from}-${relation.to}-${index}` }] : []
  }),
)
const groupFrames = computed(() =>
  diagram.value.groups.flatMap((group, index) => {
    const members = group.entityNames.flatMap((name) => {
      const entity = getEntity(name)
      return entity ? [entity] : []
    })
    if (members.length === 0) return []
    const x = Math.min(...members.map((entity) => entity.x))
    const y = Math.min(...members.map((entity) => entity.y))
    const right = Math.max(...members.map((entity) => entity.x + nodeWidth))
    const bottom = Math.max(...members.map((entity) => entity.y + nodeHeight(entity)))
    return [{
      name: group.name,
      entityNames: group.entityNames,
      colorIndex: index % 6,
      x: x - 18,
      y: y - 42,
      width: right - x + 36,
      height: bottom - y + 58,
    }]
  }),
)
const contentBounds = computed(() => {
  const entities = diagram.value.entities
  if (entities.length === 0) {
    return { left: 0, top: 0, width: minimumCanvasWidth, height: minimumCanvasHeight }
  }
  const left = Math.min(...entities.map((entity) => entity.x), ...groupFrames.value.map((group) => group.x))
  const top = Math.min(...entities.map((entity) => entity.y), ...groupFrames.value.map((group) => group.y))
  const right = Math.max(
    ...entities.map((entity) => entity.x + nodeWidth),
    ...groupFrames.value.map((group) => group.x + group.width),
  )
  const bottom = Math.max(
    ...entities.map((entity) => entity.y + nodeHeight(entity)),
    ...groupFrames.value.map((group) => group.y + group.height),
  )
  return { left, top, width: right - left, height: bottom - top }
})
const canvasBounds = computed(() => {
  const current = contentBounds.value
  const anchor = canvasAnchor.value ?? current
  const right = Math.max(anchor.left + anchor.width, current.left + current.width)
  const bottom = Math.max(anchor.top + anchor.height, current.top + current.height)
  return { left: anchor.left, top: anchor.top, width: right - anchor.left, height: bottom - anchor.top }
})
const canvasGeometry = computed(() => {
  const bounds = canvasBounds.value
  const width = (bounds.width + canvasMargin * 2) * zoom.value
  const height = (bounds.height + canvasMargin * 2) * zoom.value
  const alignment = canvasAnchor.value ?? bounds
  const alignedWidth = (alignment.width + canvasMargin * 2) * zoom.value
  const alignedHeight = (alignment.height + canvasMargin * 2) * zoom.value
  const offsetX = Math.max(0, (canvasViewportSize.value.width - alignedWidth) / 2)
    - (alignment.left - canvasMargin) * zoom.value
  const offsetY = Math.max(0, (canvasViewportSize.value.height - alignedHeight) / 2)
    - (alignment.top - canvasMargin) * zoom.value

  return {
    offsetX,
    offsetY,
    sizerStyle: {
      width: `${Math.max(canvasViewportSize.value.width, width)}px`,
      height: `${Math.max(canvasViewportSize.value.height, height)}px`,
    },
    diagramStyle: {
      width: `${canvasWidth.value}px`,
      height: `${canvasHeight.value}px`,
      transform: `translate(${offsetX}px, ${offsetY}px) scale(${zoom.value})`,
    },
  }
})

function layoutEntities(entities: Entity[], groups: EntityGroup[] = []) {
  if (groups.length > 0) {
    const positions = new Map<string, { x: number; y: number }>()
    const groupedNames = new Set(groups.flatMap((group) => group.entityNames))
    const nextGroupY = [72, 72]

    for (const [index, group] of groups.entries()) {
      const diagramColumn = index % 2
      const groupX = 62 + diagramColumn * 890
      const groupY = nextGroupY[diagramColumn]
      const columns = [groupY + 58, groupY + 58]

      for (const name of group.entityNames) {
        const entity = entities.find((candidate) => candidate.name === name)
        if (!entity) continue
        const entityColumn = columns[0] <= columns[1] ? 0 : 1
        positions.set(name, {
          x: groupX + 24 + entityColumn * 280,
          y: columns[entityColumn],
        })
        columns[entityColumn] += nodeHeight(entity) + 22
      }

      nextGroupY[diagramColumn] = Math.max(...columns) + 26
    }

    const ungrouped = entities.filter((entity) => !groupedNames.has(entity.name))
    const ungroupedY = Math.max(...nextGroupY) + 12
    for (const [index, entity] of ungrouped.entries()) {
      positions.set(entity.name, {
        x: 76 + (index % 5) * 350,
        y: ungroupedY + Math.floor(index / 5) * 340,
      })
    }

    return entities.map((entity) => ({
      ...entity,
      ...(positions.get(entity.name) ?? { x: 76, y: 72 }),
    }))
  }

  const columnCount = Math.max(1, Math.ceil(Math.sqrt(entities.length)))
  return entities.map((entity, index) => ({
    ...entity,
    x: 76 + (index % columnCount) * 370,
    y: 72 + Math.floor(index / columnCount) * 340,
  }))
}

function parseDiagram(input: string): Diagram {
  const lines = input.split(/\r?\n/)
  if (!/^\s*erDiagram\s*$/m.test(input)) {
    throw new Error('Start your diagram with an erDiagram declaration.')
  }

  const entities: Entity[] = []
  const relationships: Relationship[] = []
  const groups: EntityGroup[] = []
  const entityNames = new Set<string>()
  const groupNames = new Set<string>()
  const groupedEntityNames = new Set<string>()
  let activeEntity: Entity | undefined

  for (const [index, rawLine] of lines.entries()) {
    const line = rawLine.trim()
    if (!line || line === 'erDiagram') continue

    if (line.startsWith('%%')) {
      if (/^%%\s*@relate-group\b/i.test(line)) {
        if (activeEntity) {
          throw new Error(`Group directives must appear outside entities (line ${index + 1}).`)
        }
        const groupMatch = line.match(/^%%\s*@relate-group\s+(.+?)\s*:\s*(.+)$/i)
        if (!groupMatch) {
          throw new Error(`Use "%% @relate-group Group name: entity, entity" on line ${index + 1}.`)
        }
        const [, name, entityList] = groupMatch
        const groupName = name.trim()
        const members = entityList.split(',').map((member) => member.trim())
        if (!groupName || members.some((member) => !/^[A-Za-z_][\w-]*$/.test(member))) {
          throw new Error(`Group directive on line ${index + 1} needs a name and comma-separated entity names.`)
        }
        if (groupNames.has(groupName.toLocaleLowerCase())) {
          throw new Error(`Group "${groupName}" is declared more than once.`)
        }
        groupNames.add(groupName.toLocaleLowerCase())
        for (const member of members) {
          if (groupedEntityNames.has(member)) {
            throw new Error(`Entity "${member}" can only belong to one group.`)
          }
          groupedEntityNames.add(member)
        }
        groups.push({ name: groupName, entityNames: members })
      }
      continue
    }

    if (activeEntity) {
      if (line === '}') {
        activeEntity = undefined
        continue
      }

      const columnMatch = line.match(/^(\S+)\s+(.+?)(?:\s+"([^"]*)")?$/)
      if (!columnMatch) {
        throw new Error(`Could not read the attribute on line ${index + 1}.`)
      }
      const [, type, rawName, note] = columnMatch
      const parts = rawName.trim().split(/\s+/)
      const name = parts.shift()
      if (!name) {
        throw new Error(`Missing attribute name on line ${index + 1}.`)
      }
      activeEntity.columns.push({ type, name, key: parts.join(', ') || undefined, note })
      continue
    }

    const entityMatch = line.match(/^([A-Za-z_][\w-]*)\s*\{$/)
    if (entityMatch) {
      const name = entityMatch[1]
      if (entityNames.has(name)) {
        throw new Error(`Entity "${name}" is declared more than once.`)
      }
      entityNames.add(name)
      activeEntity = { name, columns: [], x: 0, y: 0 }
      entities.push(activeEntity)
      continue
    }

    const relationMatch = line.match(
      /^([A-Za-z_][\w-]*)\s+([|o}][|o{])(--[|o}][|o{])\s+([A-Za-z_][\w-]*)\s*:\s*(?:"([^"]*)"|(.+))$/,
    )
    if (relationMatch) {
      const [, from, leftMarker, rightMarker, to, quotedLabel, plainLabel] = relationMatch
      relationships.push({
        from,
        to,
        fromCardinality: leftMarker,
        toCardinality: rightMarker.slice(2),
        label: (quotedLabel ?? plainLabel).trim(),
      })
      continue
    }

    throw new Error(`Could not read the diagram syntax on line ${index + 1}.`)
  }

  if (activeEntity) {
    throw new Error(`Entity "${activeEntity.name}" is missing its closing brace.`)
  }
  if (entities.length === 0) {
    throw new Error('Add at least one entity to your diagram.')
  }

  for (const relation of relationships) {
    if (!entityNames.has(relation.from) || !entityNames.has(relation.to)) {
      throw new Error(`Relationship "${relation.from} → ${relation.to}" uses an undeclared entity.`)
    }
  }

  for (const group of groups) {
    for (const member of group.entityNames) {
      if (!entityNames.has(member)) {
        throw new Error(`Group "${group.name}" refers to undeclared entity "${member}".`)
      }
    }
  }

  return { entities: layoutEntities(entities, groups), relationships, groups }
}

function applyDiagram() {
  parseError.value = ''
  try {
    const parsed = parseDiagram(draftSource.value)
    canvasAnchor.value = undefined
    diagram.value = parsed
  } catch (error) {
    parseError.value = error instanceof Error ? error.message : 'The diagram could not be parsed.'
  }
}

function nodeHeight(entity: Entity) {
  return headerHeight + Math.max(entity.columns.length, 1) * rowHeight + nodePadding
}

function getEntity(name: string) {
  return diagram.value.entities.find((entity) => entity.name === name)
}

function relationPath(relation: Relationship) {
  const from = getEntity(relation.from)
  const to = getEntity(relation.to)
  if (!from || !to) return undefined

  const fromCenterX = from.x + nodeWidth / 2
  const toCenterX = to.x + nodeWidth / 2
  const fromCenterY = from.y + nodeHeight(from) / 2
  const toCenterY = to.y + nodeHeight(to) / 2
  const horizontal = Math.abs(toCenterX - fromCenterX) > Math.abs(toCenterY - fromCenterY)
  const startX = horizontal ? (toCenterX > fromCenterX ? from.x + nodeWidth : from.x) : fromCenterX
  const startY = horizontal ? fromCenterY : (toCenterY > fromCenterY ? from.y + nodeHeight(from) : from.y)
  const endX = horizontal ? (toCenterX > fromCenterX ? to.x : to.x + nodeWidth) : toCenterX
  const endY = horizontal ? toCenterY : (toCenterY > fromCenterY ? to.y : to.y + nodeHeight(to))
  const midX = (startX + endX) / 2
  const midY = (startY + endY) / 2

  return {
    d: horizontal
      ? `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`
      : `M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}`,
    labelX: midX,
    labelY: midY - 9,
    fromX: startX,
    fromY: startY,
    toX: endX,
    toY: endY,
  }
}

function startDrag(event: PointerEvent, entity: Entity) {
  if (handMode.value || (event.target as HTMLElement).closest('button')) return
  startEntityDrag(event, [entity])
}

function startGroupDrag(event: PointerEvent, group: { entityNames: string[] }) {
  if (handMode.value) return
  event.stopPropagation()
  const entities = group.entityNames.flatMap((name) => {
    const entity = getEntity(name)
    return entity ? [entity] : []
  })
  startEntityDrag(event, entities)
}

function startEntityDrag(event: PointerEvent, entities: Entity[]) {
  if (entities.length === 0) return
  canvasAnchor.value ??= { ...contentBounds.value }
  drag.value = {
    entities,
    positions: entities.map((entity) => ({ entity, x: entity.x, y: entity.y })),
    pointerX: event.clientX,
    pointerY: event.clientY,
  }
  ;(event.currentTarget as Element).setPointerCapture(event.pointerId)
}

function moveDrag(event: PointerEvent) {
  if (!drag.value) return
  const deltaX = (event.clientX - drag.value.pointerX) / zoom.value
  const deltaY = (event.clientY - drag.value.pointerY) / zoom.value
  const minX = Math.min(...drag.value.positions.map(({ x }) => x))
  const minY = Math.min(...drag.value.positions.map(({ y }) => y))
  const safeDeltaX = Math.max(-minX, deltaX)
  const safeDeltaY = Math.max(-minY, deltaY)

  for (const position of drag.value.positions) {
    position.entity.x = position.x + safeDeltaX
    position.entity.y = position.y + safeDeltaY
  }
}

function stopDrag() {
  drag.value = undefined
}

function isGroupDragging(group: { entityNames: string[] }) {
  return drag.value?.entities.length === group.entityNames.length
    && group.entityNames.every((name) => drag.value?.entities.some((entity) => entity.name === name))
}

function startCanvasPan(event: PointerEvent) {
  if (!handMode.value || event.button !== 0 || !canvasScroll.value) return
  if ((event.target as HTMLElement).closest('button, select')) return
  pan.value = {
    pointerX: event.clientX,
    pointerY: event.clientY,
    scrollLeft: canvasScroll.value.scrollLeft,
    scrollTop: canvasScroll.value.scrollTop,
  }
  canvasScroll.value.setPointerCapture(event.pointerId)
}

function moveCanvasPan(event: PointerEvent) {
  if (!pan.value || !canvasScroll.value) return
  canvasScroll.value.scrollLeft = pan.value.scrollLeft - (event.clientX - pan.value.pointerX)
  canvasScroll.value.scrollTop = pan.value.scrollTop - (event.clientY - pan.value.pointerY)
}

function stopCanvasPan() {
  pan.value = undefined
}

function resetLayout() {
  canvasAnchor.value = undefined
  diagram.value.entities = layoutEntities(
    diagram.value.entities.map(({ name, columns }) => ({ name, columns, x: 0, y: 0 })),
    diagram.value.groups,
  )
}

function zoomBy(amount: number) {
  zoom.value = Math.min(maximumZoom, Math.max(minimumZoom, Number((zoom.value + amount).toFixed(2))))
}

function handleCanvasWheel(event: WheelEvent) {
  if (!canvasScroll.value) return
  const viewport = canvasScroll.value
  const deltaScale = event.deltaMode === WheelEvent.DOM_DELTA_LINE
    ? 16
    : event.deltaMode === WheelEvent.DOM_DELTA_PAGE
      ? viewport.clientHeight
      : 1

  event.preventDefault()

  if (event.ctrlKey || event.metaKey) {
    const viewportRect = viewport.getBoundingClientRect()
    const pointerX = event.clientX - viewportRect.left
    const pointerY = event.clientY - viewportRect.top
    const previousZoom = zoom.value
    const anchorX = (viewport.scrollLeft + pointerX - canvasGeometry.value.offsetX) / previousZoom
    const anchorY = (viewport.scrollTop + pointerY - canvasGeometry.value.offsetY) / previousZoom
    const nextZoom = Math.min(
      maximumZoom,
      Math.max(minimumZoom, previousZoom * Math.exp((-event.deltaY * deltaScale) * 0.005)),
    )

    zoom.value = Number(nextZoom.toFixed(3))
    void nextTick(() => {
      viewport.scrollLeft = anchorX * zoom.value + canvasGeometry.value.offsetX - pointerX
      viewport.scrollTop = anchorY * zoom.value + canvasGeometry.value.offsetY - pointerY
    })
    return
  }

  viewport.scrollLeft += event.deltaX * deltaScale
  viewport.scrollTop += event.deltaY * deltaScale
}

function onKeyDown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    applyDiagram()
  }
}

watch(
  activeTheme,
  (theme) => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
  },
  { immediate: true },
)

watch(themeMode, (theme) => {
  localStorage.setItem('relate-theme', theme)
})

watch(sourceOpen, (open) => {
  localStorage.setItem('relate-source-open', String(open))
})

function updateSystemTheme(event: MediaQueryListEvent) {
  systemTheme.value = event.matches ? 'dark' : 'light'
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  systemColorScheme.addEventListener('change', updateSystemTheme)
  canvasScroll.value?.addEventListener('wheel', handleCanvasWheel, { passive: false })
  if (canvasScroll.value) {
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (!entry) return
      canvasViewportSize.value = {
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      }
    })
    observer.observe(canvasScroll.value)
    resizeObserver = observer
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  systemColorScheme.removeEventListener('change', updateSystemTheme)
  canvasScroll.value?.removeEventListener('wheel', handleCanvasWheel)
  resizeObserver?.disconnect()
})

applyDiagram()
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="#" aria-label="Relate home">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path d="M8 9h6m4 0h6M8 23h6m4 0h6M9 11v10m14-10v10M13 9h6m-6 14h6" />
            <circle cx="8" cy="9" r="2.5" />
            <circle cx="24" cy="9" r="2.5" />
            <circle cx="8" cy="23" r="2.5" />
            <circle cx="24" cy="23" r="2.5" />
          </svg>
        </span>
        <span class="brand-name">relate<span class="brand-period">.</span></span>
        <span class="brand-divider"></span>
        <span class="brand-product">ERD viewer</span>
      </a>
      <div class="topbar-right">
        <span class="saved-indicator"><span></span> Local draft</span>
        <label class="theme-control" title="Choose system, light, or dark appearance">
          <svg v-if="activeTheme === 'dark'" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M16.4 12.6A7 7 0 0 1 7.4 3.6a7 7 0 1 0 9 9Z" />
          </svg>
          <svg v-else viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <circle cx="10" cy="10" r="3.25" />
            <path d="M10 1.75v2m0 12.5v2m8.25-8.25h-2m-12.5 0h-2m14.08-5.83-1.42 1.42M5.59 14.41l-1.42 1.42m11.66 0-1.42-1.42M5.59 5.59 4.17 4.17" />
          </svg>
          <select v-model="themeMode" aria-label="Color theme">
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
          <svg class="theme-chevron" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="m3 4.5 3 3 3-3" />
          </svg>
        </label>
        <span class="avatar">JM</span>
      </div>
    </header>

    <main class="workspace">
      <section class="canvas-panel" aria-label="Diagram canvas">
        <div class="canvas-header">
          <div class="document-heading">
            <div class="breadcrumbs"><span>My diagrams</span><span class="crumb-slash">/</span><strong>Application schema</strong></div>
            <div class="document-title">
              <h1>Application schema</h1>
              <span class="visibility-pill"><span></span> Local</span>
            </div>
          </div>
          <div class="canvas-actions">
            <button class="icon-button" title="Reset layout" aria-label="Reset layout" @click="resetLayout">
              <svg viewBox="0 0 20 20" fill="none"><path d="M3.5 6.5A7 7 0 1 1 3 11m.5-4.5V3m0 3.5H7" /></svg>
            </button>
            <span class="action-separator"></span>
            <button
              class="icon-button"
              :class="{ active: handMode }"
              :aria-pressed="handMode"
              :title="handMode ? 'Turn off hand tool' : 'Turn on hand tool'"
              :aria-label="handMode ? 'Turn off hand tool' : 'Turn on hand tool'"
              @click="handMode = !handMode"
            >
              <svg viewBox="0 0 20 20" fill="none">
                <path d="M6.5 10V5.25a1.25 1.25 0 0 1 2.5 0V9m0-.75V4a1.25 1.25 0 0 1 2.5 0v4.75m0-.5V5.5a1.25 1.25 0 0 1 2.5 0v6.75l.45-.9a1.4 1.4 0 0 1 2.55 1.15l-1.2 3.1A3.8 3.8 0 0 1 12.25 18h-2.1a4 4 0 0 1-3.1-1.48L4.3 13.1a1.65 1.65 0 0 1 2.2-2.43L8 12" />
              </svg>
            </button>
            <button class="icon-button" title="Zoom out" aria-label="Zoom out" @click="zoomBy(-0.1)">
              <svg viewBox="0 0 20 20" fill="none"><circle cx="8.75" cy="8.75" r="5.75" /><path d="m13 13 4 4M6 8.75h5.5" /></svg>
            </button>
            <span class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
            <button class="icon-button" title="Zoom in" aria-label="Zoom in" @click="zoomBy(0.1)">
              <svg viewBox="0 0 20 20" fill="none"><circle cx="8.75" cy="8.75" r="5.75" /><path d="m13 13 4 4M8.75 6v5.5M6 8.75h5.5" /></svg>
            </button>
            <span class="action-separator"></span>
            <button class="source-toggle" :class="{ active: sourceOpen }" @click="sourceOpen = !sourceOpen">
              <svg viewBox="0 0 20 20" fill="none"><path d="m7 5-5 5 5 5m6-10 5 5-5 5m-2-12-2 14" /></svg>
              <span>{{ sourceOpen ? 'Hide source' : 'View source' }}</span>
            </button>
          </div>
        </div>

        <div class="diagram-meta">
          <div class="diagram-meta-left">
            <span class="meta-dot"></span>
            <span>{{ entityCount }} entities</span>
            <span class="meta-divider">·</span>
            <span>{{ relationshipCount }} relationships</span>
            <template v-if="groupCount > 0">
              <span class="meta-divider">·</span>
              <span>{{ groupCount }} groups</span>
            </template>
          </div>
          <span class="drag-hint"><svg viewBox="0 0 16 16" fill="none"><path d="M8 1.5v13M1.5 8h13M5.5 4 8 1.5 10.5 4M5.5 12 8 14.5l2.5-2.5M4 5.5 1.5 8 4 10.5m8-5L14.5 8 12 10.5" /></svg> Drag to arrange</span>
        </div>

        <div class="canvas-viewport" :class="{ 'with-source': sourceOpen }">
          <div
            ref="canvasScroll"
            class="canvas-scroll"
            :class="{ 'hand-mode': handMode, panning: pan }"
            @pointerdown="startCanvasPan"
            @pointermove="moveCanvasPan"
            @pointerup="stopCanvasPan"
            @pointercancel="stopCanvasPan"
          >
            <div
              class="canvas-sizer"
              :style="canvasGeometry.sizerStyle"
            >
              <div
              class="diagram-canvas"
              :style="canvasGeometry.diagramStyle"
              >
              <svg class="relations-layer" :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`" aria-hidden="true">
                <defs>
                  <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#a8b0bd" />
                  </marker>
                </defs>
                <g
                  v-for="group in groupFrames"
                  :key="group.name"
                  class="group-frame"
                  :class="[`group-tone-${group.colorIndex}`, { dragging: isGroupDragging(group) }]"
                  @pointerdown="startGroupDrag($event, group)"
                  @pointermove="moveDrag"
                  @pointerup="stopDrag"
                  @pointercancel="stopDrag"
                >
                  <rect
                    :x="group.x"
                    :y="group.y"
                    :width="group.width"
                    :height="group.height"
                    rx="12"
                    class="group-outline"
                  />
                  <text :x="group.x + 18" :y="group.y + 24" class="group-title">{{ group.name }}</text>
                </g>
                <g v-for="{ path, key } in renderedRelationships" :key="key">
                  <path
                    :d="path.d"
                    class="relation-line"
                    marker-start="url(#arrow)"
                    marker-end="url(#arrow)"
                  />
                </g>
              </svg>

              <article
                v-for="(entity, entityIndex) in diagram.entities"
                :key="entity.name"
                class="entity-card"
                :class="{ dragging: drag?.entities.includes(entity) }"
                :style="{ left: `${entity.x}px`, top: `${entity.y}px`, width: `${nodeWidth}px` }"
                @pointerdown="startDrag($event, entity)"
                @pointermove="moveDrag"
                @pointerup="stopDrag"
                @pointercancel="stopDrag"
              >
                <header class="entity-header" :class="`entity-tone-${entityIndex % 6}`">
                  <span class="entity-icon"><svg viewBox="0 0 16 16" fill="none"><rect x="2.25" y="2.25" width="11.5" height="11.5" rx="2" /><path d="M5 5.25h6m-6 2.75h6M5 10.75h3" /></svg></span>
                  <span class="entity-name">{{ entity.name }}</span>
                  <button class="entity-menu" :aria-label="`More options for ${entity.name}`" @pointerdown.stop>
                    <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1" /><circle cx="8" cy="8" r="1" /><circle cx="13" cy="8" r="1" /></svg>
                  </button>
                </header>
                <div class="entity-columns">
                  <div v-for="column in entity.columns" :key="column.name" class="column-row">
                    <span class="column-type">{{ column.type }}</span>
                    <span class="column-name">{{ column.name }}</span>
                    <span v-if="column.key" class="column-key" :class="{ 'key-primary': column.key.includes('PK') }">{{ column.key }}</span>
                    <span v-else-if="column.note" class="column-key nullable">NULL</span>
                    <span v-if="column.note && column.key" class="column-note">{{ column.note }}</span>
                  </div>
                  <div v-if="entity.columns.length === 0" class="empty-entity">No attributes</div>
                </div>
                <footer class="entity-footer"><span>{{ entity.columns.length }} fields</span><span class="entity-footer-dot">·</span><span>Entity</span></footer>
              </article>
              <svg
                class="relation-labels-layer"
                :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`"
                aria-hidden="true"
              >
                <g v-for="{ relation, path, key } in renderedRelationships" :key="key">
                  <rect
                    :x="path.labelX - 76"
                    :y="path.labelY - 11"
                    width="152"
                    height="21"
                    rx="6"
                    class="relation-label-bg"
                  />
                  <text :x="path.labelX" :y="path.labelY + 4" class="relation-label">
                    {{ relation.label }}
                  </text>
                  <text :x="path.fromX + 8" :y="path.fromY - 7" class="cardinality">
                    {{ relation.fromCardinality }}
                  </text>
                  <text :x="path.toX - 8" :y="path.toY - 7" text-anchor="end" class="cardinality">
                    {{ relation.toCardinality }}
                  </text>
                </g>
              </svg>
              </div>
            </div>
          </div>
          <div v-if="diagram.entities.length === 0" class="empty-state">
            <div class="empty-state-icon"><svg viewBox="0 0 32 32" fill="none"><rect x="3" y="4" width="11" height="9" rx="2" /><rect x="18" y="19" width="11" height="9" rx="2" /><path d="M14 8.5h5a3 3 0 0 1 3 3V19" /></svg></div>
            <h2>Your diagram is ready to take shape</h2>
            <p>Paste a Mermaid <code>erDiagram</code> to get started.</p>
          </div>
        </div>

        <div class="canvas-footer">
          <span><kbd>⌘</kbd><span class="plus-key">+</span><kbd>↵</kbd> to apply changes</span>
          <span class="footer-status"><span></span> Mermaid ER diagram</span>
        </div>
      </section>

      <aside v-if="sourceOpen" class="source-panel" aria-label="Mermaid source editor">
        <div class="source-panel-header">
          <div class="source-title-wrap">
            <span class="source-file-icon"><svg viewBox="0 0 18 18" fill="none"><path d="M4 2.75h6.25L14.5 7v8.25H4z" /><path d="M10 2.75V7h4.25M6.5 10h5m-5 2.5h5" /></svg></span>
            <div><h2>Diagram source</h2><p>Mermaid syntax</p></div>
          </div>
          <span class="source-badge">.mmd</span>
        </div>
        <div class="editor-toolbar">
          <span><span class="editor-dot"></span> application-schema.mmd</span>
          <span>{{ editorLineCount }} lines</span>
        </div>
        <div class="editor-wrap" :class="{ 'has-error': parseError }">
          <div class="line-numbers" aria-hidden="true">
            <span v-for="line in editorLineCount" :key="line">{{ line }}</span>
          </div>
          <textarea
            v-model="draftSource"
            class="source-editor"
            spellcheck="false"
            aria-label="Mermaid diagram source"
            @keydown.meta.enter.prevent="applyDiagram"
            @keydown.ctrl.enter.prevent="applyDiagram"
          ></textarea>
        </div>
        <div class="source-bottom">
          <div v-if="parseError" class="parse-error" role="alert">
            <svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" /><path d="M8 4.75v3.5m0 2.5h.01" /></svg>
            <span>{{ parseError }}</span>
          </div>
          <div v-else class="editor-help"><span class="success-check">✓</span> <span>Diagram is up to date</span></div>
          <button class="apply-button" @click="applyDiagram">
            <span>Apply changes</span>
            <kbd>⌘ ↵</kbd>
          </button>
        </div>
      </aside>
    </main>
    <div class="toast-slot" aria-live="polite"></div>
  </div>
</template>
