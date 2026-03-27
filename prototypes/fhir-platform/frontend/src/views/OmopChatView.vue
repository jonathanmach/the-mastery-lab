<script setup lang="ts">
import { ref, nextTick } from 'vue'
import OmopChart from '../components/OmopChart.vue'
import type { ChartSpec } from '../api/types'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sql?: string
  columns?: string[]
  results?: Record<string, unknown>[]
  rowCount?: number
  insight?: string
  chartSpec?: ChartSpec | null
  error?: string
}

const messages = ref<Message[]>([])
const sqlOpen = ref<Record<number, boolean>>({})
const chartView = ref<Record<number, 'table' | 'chart'>>({})
const input = ref('')
const loading = ref(false)
const chatEl = ref<HTMLElement | null>(null)

function toggleSql(i: number) {
  sqlOpen.value[i] = !sqlOpen.value[i]
}

function currentView(i: number, msg: Message): 'table' | 'chart' {
  return chartView.value[i] ?? (msg.chartSpec ? 'chart' : 'table')
}

const EXAMPLES_POPULATION = [
  'How many patients are in the database?',
  'What are the top 10 most common conditions?',
  'Show average BMI by gender',
  'How many patients have diabetes?',
  'What is the distribution of patients by year of birth?',
]

const EXAMPLES_PERSONAL = [
  'What conditions do I have?',
  'What medications am I currently taking?',
  'How many visits have I had?',
  'Show my latest measurements',
  'How do my visits compare to the average patient?',
]

async function send() {
  const question = input.value.trim()
  if (!question || loading.value) return

  messages.value.push({ role: 'user', content: question })
  input.value = ''
  loading.value = true
  await scrollToBottom()

  // Build conversation history for context (text-only turns)
  const history = messages.value
    .slice(0, -1)
    .filter(m => m.role === 'user' || (m.role === 'assistant' && !m.error))
    .map(m => ({
      role: m.role,
      content: m.role === 'assistant'
        ? `SQL: ${m.sql}\nReturned ${m.rowCount} rows.`
        : m.content,
    }))

  try {
    const res = await fetch('/omop/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history }),
    })
    let data: Record<string, unknown> = {}
    try {
      data = await res.json()
    } catch {
      messages.value.push({ role: 'assistant', content: '', error: 'Server returned an invalid response. Please try again.' })
      return
    }
    if (!res.ok) {
      messages.value.push({ role: 'assistant', content: '', error: String(data.detail ?? 'Unknown error') })
    } else {
      messages.value.push({
        role: 'assistant',
        content: question,
        sql: data.sql as string,
        columns: data.columns as string[],
        results: data.results as Record<string, unknown>[],
        rowCount: data.row_count as number,
        insight: data.insight as string,
        chartSpec: (data.chart_spec as ChartSpec) ?? null,
      })
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '', error: String(e) })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  chatEl.value?.scrollTo({ top: chatEl.value.scrollHeight, behavior: 'smooth' })
}

function useExample(q: string) {
  input.value = q
  send()
}

function formatCell(val: unknown): string {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'number') return Number.isInteger(val) ? String(val) : val.toFixed(2)
  return String(val)
}
</script>

<template>
  <div class="omop-chat">
    <div class="chat-sidebar">
      <div class="sidebar-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M4 6h16M4 10h16M4 14h10" stroke-linecap="round"/>
        </svg>
        OMOP Analytics
      </div>
      <p class="sidebar-desc">Ask questions in plain English. Claude generates SQL and runs it against the OMOP CDM database.</p>
      <div class="examples-label">My data</div>
      <button
        v-for="q in EXAMPLES_PERSONAL"
        :key="q"
        class="example-btn"
        @click="useExample(q)"
        :disabled="loading"
      >{{ q }}</button>

      <div class="examples-label" style="margin-top: 8px">Population</div>
      <button
        v-for="q in EXAMPLES_POPULATION"
        :key="q"
        class="example-btn"
        @click="useExample(q)"
        :disabled="loading"
      >{{ q }}</button>

      <div class="schema-hint">
        <div class="schema-hint-title">Schema</div>
        <div class="schema-table" v-for="t in ['person', 'visit_occurrence', 'condition_occurrence', 'drug_exposure', 'measurement', 'observation']" :key="t">
          {{ t }}
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div class="chat-messages" ref="chatEl">
        <div v-if="messages.length === 0" class="chat-empty">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5" stroke-linecap="round"/>
            <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            <path d="M12 8v.01M12 12v4" stroke-linecap="round"/>
          </svg>
          <p>Ask a question about the OMOP database</p>
          <p class="empty-sub">Try one of the examples on the left to get started</p>
        </div>

        <template v-for="(msg, i) in messages" :key="i">
          <!-- User message -->
          <div v-if="msg.role === 'user'" class="msg msg-user">
            <div class="msg-bubble">{{ msg.content }}</div>
          </div>

          <!-- Assistant message -->
          <div v-else class="msg msg-assistant">
            <div v-if="msg.error" class="msg-error">
              <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
              <pre>{{ msg.error }}</pre>
            </div>

            <template v-else>
              <div class="sql-block">
                <button class="sql-toggle" @click="toggleSql(i)">
                  <svg viewBox="0 0 16 16" fill="currentColor">
                    <path d="M6 3.5l4 4-4 4" v-if="!sqlOpen[i]" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M3.5 6l4 4 4-4" v-else stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Generated SQL
                </button>
                <pre v-if="sqlOpen[i]" class="sql-code">{{ msg.sql }}</pre>
              </div>

              <div class="result-meta">
                {{ msg.rowCount }} row{{ msg.rowCount === 1 ? '' : 's' }} returned
              </div>

              <div v-if="msg.chartSpec" class="view-toggle">
                <button
                  :class="['toggle-btn', { active: currentView(i, msg) === 'table' }]"
                  @click="chartView[i] = 'table'"
                >Table</button>
                <button
                  :class="['toggle-btn', { active: currentView(i, msg) === 'chart' }]"
                  @click="chartView[i] = 'chart'"
                >Chart</button>
              </div>

              <template v-if="currentView(i, msg) === 'table'">
                <div v-if="msg.results && msg.results.length > 0" class="result-table-wrap">
                  <table class="result-table">
                    <thead>
                      <tr>
                        <th v-for="col in msg.columns" :key="col">{{ col }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, ri) in msg.results" :key="ri">
                        <td v-for="col in msg.columns" :key="col">{{ formatCell(row[col]) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else-if="msg.results" class="no-rows">No rows returned</div>
              </template>

              <OmopChart
                v-if="msg.chartSpec && currentView(i, msg) === 'chart'"
                :spec="msg.chartSpec"
                :results="msg.results ?? []"
              />

              <div v-if="msg.insight" class="insight-block">
                <div class="insight-icon">
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10 2a6 6 0 00-3.93 10.54c.27.25.43.6.43.96V15a1 1 0 001 1h5a1 1 0 001-1v-1.5c0-.36.16-.71.43-.96A6 6 0 0010 2z"/>
                    <path d="M8 17h4v1a1 1 0 01-1 1H9a1 1 0 01-1-1v-1z"/>
                  </svg>
                </div>
                <p class="insight-text">{{ msg.insight }}</p>
              </div>
            </template>
          </div>
        </template>

        <div v-if="loading" class="msg msg-assistant">
          <div class="thinking">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <div class="chat-input-bar">
        <textarea
          v-model="input"
          class="chat-input"
          placeholder="Ask a question about the OMOP data…"
          rows="1"
          :disabled="loading"
          @keydown.enter.exact.prevent="send"
        />
        <button class="send-btn" :disabled="!input.trim() || loading" @click="send">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.omop-chat {
  display: flex;
  height: calc(100vh - 52px);
  overflow: hidden;
  background: #f8fafc;
}

/* Sidebar */
.chat-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: #1e293b;
  color: #f8fafc;
  padding: 20px 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 14px;
  color: #f8fafc;
}
.sidebar-title svg { width: 18px; height: 18px; color: #60a5fa; flex-shrink: 0; }
.sidebar-desc { font-size: 12px; color: #94a3b8; line-height: 1.5; margin: 0; }
.examples-label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.6px; margin-top: 4px; }
.example-btn {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 6px;
  color: #cbd5e1;
  font-size: 12px;
  padding: 8px 10px;
  text-align: left;
  cursor: pointer;
  line-height: 1.4;
  transition: background 0.15s;
}
.example-btn:hover:not(:disabled) { background: rgba(255,255,255,0.1); color: #f8fafc; }
.example-btn:disabled { opacity: 0.5; cursor: default; }

.schema-hint { margin-top: auto; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08); }
.schema-hint-title { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px; }
.schema-table { font-size: 11px; color: #475569; font-family: monospace; padding: 2px 0; }

/* Main chat area */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Empty state */
.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  text-align: center;
  padding: 40px;
}
.empty-icon { width: 40px; height: 40px; color: #cbd5e1; margin-bottom: 12px; }
.chat-empty p { margin: 4px 0; font-size: 15px; }
.empty-sub { font-size: 13px; color: #cbd5e1; }

/* Messages */
.msg { display: flex; flex-direction: column; max-width: 900px; }
.msg-user { align-self: flex-end; align-items: flex-end; }
.msg-bubble {
  background: #2563eb;
  color: #fff;
  border-radius: 16px 16px 4px 16px;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  max-width: 480px;
}

.msg-assistant { align-self: flex-start; width: 100%; }

.msg-error {
  display: flex;
  gap: 10px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 12px;
  color: #991b1b;
}
.msg-error svg { width: 16px; height: 16px; flex-shrink: 0; margin-top: 2px; }
.msg-error pre { font-size: 12px; margin: 0; white-space: pre-wrap; word-break: break-word; }

.sql-block {
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}
.sql-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 7px 12px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: color 0.15s;
}
.sql-toggle:hover { color: #94a3b8; }
.sql-toggle svg { width: 14px; height: 14px; flex-shrink: 0; }
.sql-code {
  margin: 0;
  padding: 12px;
  font-size: 12px;
  color: #7dd3fc;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.result-meta { font-size: 12px; color: #64748b; margin-bottom: 8px; }

.result-table-wrap {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.result-table th {
  background: #f1f5f9;
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  color: #475569;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  white-space: nowrap;
  border-bottom: 1px solid #e2e8f0;
}
.result-table td {
  padding: 7px 12px;
  color: #1e293b;
  border-bottom: 1px solid #f1f5f9;
  white-space: nowrap;
}
.result-table tr:last-child td { border-bottom: none; }
.result-table tbody tr:hover td { background: #f8fafc; }

.no-rows { font-size: 13px; color: #94a3b8; font-style: italic; }

.insight-block {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: 10px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 10px 14px;
}
.insight-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  color: #0284c7;
  margin-top: 1px;
}
.insight-icon svg { width: 100%; height: 100%; }
.insight-text {
  margin: 0;
  font-size: 13.5px;
  line-height: 1.6;
  color: #0c4a6e;
}

/* Thinking dots */
.thinking {
  display: flex;
  gap: 5px;
  padding: 12px 4px;
}
.thinking span {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  animation: bounce 1.2s ease-in-out infinite;
}
.thinking span:nth-child(2) { animation-delay: 0.2s; }
.thinking span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
  40% { transform: translateY(-6px); opacity: 1; }
}

/* View toggle */
.view-toggle {
  display: flex;
  gap: 2px;
  background: #e2e8f0;
  border-radius: 6px;
  padding: 2px;
  width: fit-content;
  margin-bottom: 8px;
}
.toggle-btn {
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
  background: none;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.toggle-btn.active {
  background: #fff;
  color: #1e293b;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

/* Input bar */
.chat-input-bar {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 24px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
.chat-input {
  flex: 1;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  line-height: 1.5;
  color: #1e293b;
  background: #f8fafc;
  transition: border-color 0.15s;
  field-sizing: content;
  min-height: 42px;
  max-height: 140px;
}
.chat-input:focus { border-color: #2563eb; background: #fff; }
.chat-input:disabled { opacity: 0.6; }

.send-btn {
  width: 40px; height: 40px;
  border-radius: 10px;
  background: #2563eb;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.15s;
}
.send-btn:hover:not(:disabled) { background: #1d4ed8; }
.send-btn:disabled { background: #cbd5e1; cursor: default; }
.send-btn svg { width: 18px; height: 18px; color: #fff; }
</style>
