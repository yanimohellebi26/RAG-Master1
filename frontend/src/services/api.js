/**
 * API Service -- Centralized client for all backend calls.
 *
 * Every backend interaction goes through this module so that:
 * - URL management lives in one place
 * - Error handling is consistent
 * - Adding auth headers later is trivial
 */

const BASE = '/api'

/** Generic JSON POST. */
async function post(endpoint, body) {
  const res = await fetch(`${BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || res.statusText)
  }
  return res.json()
}

/** Generic JSON GET. */
async function get(endpoint) {
  const res = await fetch(`${BASE}${endpoint}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || res.statusText)
  }
  return res.json()
}

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

export function fetchConfig() {
  return get('/config')
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

/**
 * Send a chat message and return a ReadableStream reader for SSE parsing.
 * The caller is responsible for reading the stream.
 */
export async function sendChatMessage(payload) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || res.statusText)
  }
  return res.body.getReader()
}

export function clearChat() {
  return post('/clear', {})
}

// ---------------------------------------------------------------------------
// Copilot
// ---------------------------------------------------------------------------

export function generateCopilotTool({ toolType, content, model, sources }) {
  return post('/copilot', {
    tool_type: toolType,
    content,
    model,
    sources,
  })
}

// ---------------------------------------------------------------------------
// Evaluation
// ---------------------------------------------------------------------------

export function runEvaluation() {
  return post('/eval/run', {})
}

export function fetchLatestEval() {
  return get('/eval/latest')
}

export function fetchEvalHistory() {
  return get('/eval/history')
}
