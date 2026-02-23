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

// ---------------------------------------------------------------------------
// YouTube
// ---------------------------------------------------------------------------

export function fetchYouTubeStatus() {
  return get('/youtube/status')
}

export function fetchYouTubeTranscript(payload) {
  return post('/youtube/transcript', payload)
}

export function indexYouTubeTranscript(payload) {
  return post('/youtube/index', payload)
}

export function searchYouTubeVideos(payload) {
  return post('/youtube/search', payload)
}

export function fetchYouTubeHistory(subject) {
  const qs = subject ? `?subject=${encodeURIComponent(subject)}` : ''
  return get(`/youtube/history${qs}`)
}

export async function deleteYouTubeVideo(videoId) {
  const res = await fetch(`${BASE}/youtube/history/${encodeURIComponent(videoId)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || res.statusText)
  }
  return res.json()
}

/**
 * Stream an AI analysis of a YouTube video via SSE.
 * Returns a ReadableStream reader for the caller to consume.
 */
export async function analyzeYouTubeStream(payload) {
  const res = await fetch(`${BASE}/youtube/analyze/stream`, {
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

// ---------------------------------------------------------------------------
// Notion
// ---------------------------------------------------------------------------

export function fetchNotionStatus() {
  return get('/notion/status')
}

export function connectNotion() {
  return post('/notion/connect', {})
}

export function saveToNotion(payload) {
  return post('/notion/save-synthesis', payload)
}

export function searchNotionPages(payload) {
  return post('/notion/search', payload)
}

export function fetchNotionPages() {
  return get('/notion/pages')
}

export function syncNotionPages(payload) {
  return post('/notion/sync', payload || {})
}

export function syncNotionSelectedPages(pageIds) {
  return post('/notion/sync', { page_ids: pageIds })
}

// ---------------------------------------------------------------------------
// Google Drive
// ---------------------------------------------------------------------------

export function fetchGDriveStatus() {
  return get('/gdrive/status')
}

export function connectGDrive() {
  return post('/gdrive/connect', {})
}

export function fetchGDriveFiles(folderId, query) {
  const params = new URLSearchParams()
  if (folderId) params.set('folder_id', folderId)
  if (query) params.set('query', query)
  const qs = params.toString()
  return get(`/gdrive/files${qs ? `?${qs}` : ''}`)
}

export function previewGDriveFile(fileId) {
  return get(`/gdrive/file/${encodeURIComponent(fileId)}/preview`)
}

export function syncGDriveFolder(payload) {
  return post('/gdrive/sync', payload)
}
