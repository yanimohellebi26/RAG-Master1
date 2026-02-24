/**
 * YouTubePage -- Page dediee a l'analyse de videos YouTube.
 *
 * Deux modes :
 *   1. Analyse : coller un lien → transcription + resume/concepts/analyse IA (streaming)
 *   2. Indexation : coller un lien + choisir matiere → indexer dans ChromaDB
 */

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useApp } from '../contexts/AppContext'
import {
  fetchYouTubeStatus,
  fetchYouTubeTranscript,
  indexYouTubeTranscript,
  analyzeYouTubeStream,
  fetchYouTubeHistory,
  deleteYouTubeVideo,
} from '../services/api'
import './YouTubePage.css'

function renderMarkdown(text) {
  return DOMPurify.sanitize(marked(text || ''), { USE_PROFILES: { html: true } })
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m${s.toString().padStart(2, '0')}s`
}

/* ── Inline SVG icons ─────────────────────────────────────────────────────── */

const IconFilm = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="20" height="20" rx="2" ry="2"/>
    <line x1="7" y1="2" x2="7" y2="22"/>
    <line x1="17" y1="2" x2="17" y2="22"/>
    <line x1="2" y1="12" x2="22" y2="12"/>
    <line x1="2" y1="7" x2="7" y2="7"/>
    <line x1="2" y1="17" x2="7" y2="17"/>
    <line x1="17" y1="17" x2="22" y2="17"/>
    <line x1="17" y1="7" x2="22" y2="7"/>
  </svg>
)

const IconPlay = ({ size = 16 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="5 3 19 12 5 21 5 3"/>
  </svg>
)

const IconSearch = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
)

const IconDownload = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
)

const IconDocumentText = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
)

const IconLibrary = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
  </svg>
)

const IconClipboard = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
  </svg>
)

const IconLightbulb = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="9" y1="18" x2="15" y2="18"/>
    <line x1="10" y1="22" x2="14" y2="22"/>
    <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1.45.56 2.75 1.5 3.5.76.76 1.23 1.52 1.41 2.5"/>
  </svg>
)

const IconChartBar = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10"/>
    <line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6" y1="20" x2="6" y2="14"/>
    <line x1="2" y1="20" x2="22" y2="20"/>
  </svg>
)

const IconPlayCircle = ({ size = 16 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <polygon points="10 8 16 12 10 16 10 8"/>
  </svg>
)

const IconXCircle = ({ size = 18 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="15" y1="9" x2="9" y2="15"/>
    <line x1="9" y1="9" x2="15" y2="15"/>
  </svg>
)

const IconCheckCircle = ({ size = 40 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
    <polyline points="22 4 12 14.01 9 11.01"/>
  </svg>
)

const IconAlertTriangle = ({ size = 40 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
)

const IconInbox = ({ size = 48 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>
    <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
  </svg>
)

const IconRefresh = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
)

const IconCube = ({ size = 14 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
    <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
    <line x1="12" y1="22.08" x2="12" y2="12"/>
  </svg>
)

const IconCalendar = ({ size = 14 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/>
    <line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
)

const IconTrash = ({ size = 15 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
    <path d="M10 11v6"/>
    <path d="M14 11v6"/>
    <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
)

/* ── Component ────────────────────────────────────────────────────────────── */

export default function YouTubePage() {
  const { config } = useApp()

  const [url, setUrl] = useState('')
  const [mode, setMode] = useState('analyze') // 'analyze' | 'index' | 'transcript' | 'history'
  const [analysisType, setAnalysisType] = useState('summary')
  const [subject, setSubject] = useState('')
  const [docType, setDocType] = useState('Video')

  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)
  const [transcript, setTranscript] = useState(null)
  const [analysis, setAnalysis] = useState('')
  const [indexResult, setIndexResult] = useState(null)
  const [error, setError] = useState('')
  const [streaming, setStreaming] = useState(false)

  // History state
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyFilter, setHistoryFilter] = useState('')
  const [historySearch, setHistorySearch] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  const analysisEndRef = useRef(null)

  // Check service status on mount
  useEffect(() => {
    fetchYouTubeStatus()
      .then(setStatus)
      .catch(() => setStatus({ available: false }))
  }, [])

  // Auto-scroll while streaming
  useEffect(() => {
    if (streaming) {
      analysisEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [analysis, streaming])

  // Load history when switching to history tab
  const loadHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const data = await fetchYouTubeHistory(historyFilter || undefined)
      setHistory(data.videos || [])
    } catch (err) {
      setError(err.message || 'Erreur lors du chargement de l\'historique')
    } finally {
      setHistoryLoading(false)
    }
  }, [historyFilter])

  useEffect(() => {
    if (mode === 'history') {
      loadHistory()
    }
  }, [mode, loadHistory])

  const handleDelete = async (videoId) => {
    if (deletingId) return
    setDeletingId(videoId)
    try {
      await deleteYouTubeVideo(videoId)
      setHistory(prev => prev.filter(v => v.video_id !== videoId))
    } catch (err) {
      setError(err.message || 'Erreur lors de la suppression')
    } finally {
      setDeletingId(null)
    }
  }

  // Filtered history based on search text
  const filteredHistory = history.filter(v => {
    if (!historySearch) return true
    const q = historySearch.toLowerCase()
    return (
      (v.video_id || '').toLowerCase().includes(q) ||
      (v.title || '').toLowerCase().includes(q) ||
      (v.subject || '').toLowerCase().includes(q) ||
      (v.doc_type || '').toLowerCase().includes(q)
    )
  })

  const reset = () => {
    setTranscript(null)
    setAnalysis('')
    setIndexResult(null)
    setError('')
  }

  const handleAnalyze = async () => {
    if (!url.trim()) return
    reset()
    setLoading(true)
    setStreaming(true)

    try {
      const reader = await analyzeYouTubeStream({
        video_url: url.trim(),
        analysis_type: analysisType,
      })

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          let data
          try {
            data = JSON.parse(line.slice(6))
          } catch {
            continue
          }

          if (data.type === 'transcript') {
            setTranscript(data)
          } else if (data.type === 'token') {
            setAnalysis(prev => prev + data.content)
          } else if (data.type === 'error') {
            setError(data.message)
          }
          // 'done' just means stream ended
        }
      }
    } catch (err) {
      setError(err.message || 'Erreur lors de l\'analyse')
    } finally {
      setLoading(false)
      setStreaming(false)
    }
  }

  const handleGetTranscript = async () => {
    if (!url.trim()) return
    reset()
    setLoading(true)

    try {
      const data = await fetchYouTubeTranscript({ video_url: url.trim() })
      setTranscript(data)
    } catch (err) {
      setError(err.message || 'Erreur lors de la récupération')
    } finally {
      setLoading(false)
    }
  }

  const handleIndex = async () => {
    if (!url.trim() || !subject) return
    reset()
    setLoading(true)

    try {
      const data = await indexYouTubeTranscript({
        video_url: url.trim(),
        subject,
        doc_type: docType,
      })
      setIndexResult(data)
      // Refresh history cache so the badge updates
      fetchYouTubeHistory().then(h => setHistory(h.videos || [])).catch(() => {})
    } catch (err) {
      setError(err.message || 'Erreur lors de l\'indexation')
    } finally {
      setLoading(false)
    }
  }

  const subjects = config?.subjects || []

  return (
    <div className="youtube-page">
      {/* Header */}
      <div className="yt-header">
        <div className="yt-header-icon"><IconFilm /></div>
        <div>
          <h2>YouTube Transcript</h2>
          <p className="yt-header-subtitle">
            Transcrivez, analysez et indexez des vidéos YouTube pour enrichir vos révisions
          </p>
        </div>
        {status && (
          <span className={`badge ${status.available ? 'badge-success' : 'badge-error'}`}>
            {status.available ? 'Service actif' : 'Non disponible'}
          </span>
        )}
      </div>

      {/* Input section */}
      <div className="yt-input-section">
        <div className="yt-url-row">
          <div className="yt-url-input-wrapper">
            <span className="yt-url-icon"><IconPlay /></span>
            <input
              type="text"
              className="yt-url-input"
              placeholder="Collez un lien YouTube ici... (ex: https://youtube.com/watch?v=...)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  mode === 'analyze' ? handleAnalyze() : handleIndex()
                }
              }}
              disabled={loading}
            />
          </div>
        </div>

        {/* Mode tabs */}
        <div className="yt-mode-tabs">
          <button
            className={`yt-mode-tab ${mode === 'analyze' ? 'active' : ''}`}
            onClick={() => setMode('analyze')}
          >
            <IconSearch /> Analyser
          </button>
          <button
            className={`yt-mode-tab ${mode === 'index' ? 'active' : ''}`}
            onClick={() => setMode('index')}
          >
            <IconDownload /> Indexer dans ChromaDB
          </button>
          <button
            className={`yt-mode-tab ${mode === 'transcript' ? 'active' : ''}`}
            onClick={() => setMode('transcript')}
          >
            <IconDocumentText /> Transcription brute
          </button>
          <button
            className={`yt-mode-tab ${mode === 'history' ? 'active' : ''}`}
            onClick={() => setMode('history')}
          >
            <IconLibrary /> Historique
            {history.length > 0 && <span className="yt-tab-badge">{history.length}</span>}
          </button>
        </div>

        {/* Mode-specific options */}
        {mode === 'analyze' && (
          <div className="yt-options">
            <div className="yt-option-group">
              <label>Type d'analyse</label>
              <div className="yt-analysis-chips">
                {[
                  { id: 'summary', icon: <IconClipboard />, label: 'Résumé', desc: 'Résumé structuré' },
                  { id: 'concepts', icon: <IconLightbulb />, label: 'Concepts', desc: 'Concepts clés' },
                  { id: 'detailed', icon: <IconChartBar />, label: 'Détaillée', desc: 'Analyse complète' },
                ].map(opt => (
                  <button
                    key={opt.id}
                    className={`yt-chip ${analysisType === opt.id ? 'active' : ''}`}
                    onClick={() => setAnalysisType(opt.id)}
                  >
                    {opt.icon} {opt.label}
                    <small>{opt.desc}</small>
                  </button>
                ))}
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleAnalyze}
              disabled={!url.trim() || loading}
            >
              {loading
                ? <><span className="spinner" /> Analyse en cours...</>
                : <><IconPlayCircle size={16} /> Analyser la vidéo</>}
            </button>
          </div>
        )}

        {mode === 'index' && (
          <div className="yt-options">
            <div className="yt-option-row">
              <div className="yt-option-group">
                <label>Matière *</label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="select-input"
                >
                  <option value="">-- Choisir une matière --</option>
                  {subjects.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className="yt-option-group">
                <label>Type de document</label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="select-input"
                >
                  <option value="Video">Vidéo</option>
                  <option value="CM">Cours Magistral</option>
                  <option value="TD">TD</option>
                  <option value="TP">TP</option>
                </select>
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleIndex}
              disabled={!url.trim() || !subject || loading}
            >
              {loading
                ? <><span className="spinner" /> Indexation en cours...</>
                : <><IconDownload size={16} /> Indexer dans ChromaDB</>}
            </button>
          </div>
        )}

        {mode === 'transcript' && (
          <div className="yt-options">
            <button
              className="btn btn-primary"
              onClick={handleGetTranscript}
              disabled={!url.trim() || loading}
            >
              {loading
                ? <><span className="spinner" /> Récupération...</>
                : <><IconDocumentText size={16} /> Récupérer la transcription</>}
            </button>
          </div>
        )}

        {mode === 'history' && (
          <div className="yt-options yt-history-controls">
            <div className="yt-option-row">
              <div className="yt-option-group">
                <label>Filtrer par matière</label>
                <select
                  value={historyFilter}
                  onChange={(e) => setHistoryFilter(e.target.value)}
                  className="select-input"
                >
                  <option value="">Toutes les matières</option>
                  {subjects.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className="yt-option-group yt-search-group">
                <label>Rechercher</label>
                <input
                  type="text"
                  className="yt-search-input"
                  placeholder="Rechercher par titre, ID, matière..."
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                />
              </div>
            </div>
            <button
              className="btn btn-secondary"
              onClick={loadHistory}
              disabled={historyLoading}
            >
              {historyLoading
                ? <><span className="spinner" /> Chargement...</>
                : <><IconRefresh /> Actualiser</>}
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="yt-error">
          <span><IconXCircle /></span>
          <p>{error}</p>
        </div>
      )}

      {/* Results */}
      <div className="yt-results">
        {/* Transcript metadata card */}
        {transcript && (
          <div className="yt-meta-card">
            <div className="yt-meta-row">
              <div className="yt-meta-item">
                <span className="yt-meta-label">ID Vidéo</span>
                <span className="yt-meta-value">{transcript.video_id}</span>
              </div>
              <div className="yt-meta-item">
                <span className="yt-meta-label">Langue</span>
                <span className="yt-meta-value">{transcript.language}</span>
              </div>
              {transcript.duration_seconds > 0 && (
                <div className="yt-meta-item">
                  <span className="yt-meta-label">Durée</span>
                  <span className="yt-meta-value">{formatDuration(transcript.duration_seconds)}</span>
                </div>
              )}
              <div className="yt-meta-item">
                <span className="yt-meta-label">Caractères</span>
                <span className="yt-meta-value">
                  {(transcript.transcript_length || transcript.full_text?.length || 0).toLocaleString()}
                </span>
              </div>
            </div>
            {transcript.url && (
              <a
                className="yt-video-link"
                href={transcript.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <IconPlay size={14} /> Voir la vidéo sur YouTube
              </a>
            )}
          </div>
        )}

        {/* Streaming analysis */}
        {(analysis || streaming) && (
          <div className="yt-analysis-card">
            <h3>
              {analysisType === 'summary' && <><IconClipboard size={16} /> Résumé</>}
              {analysisType === 'concepts' && <><IconLightbulb size={16} /> Concepts clés</>}
              {analysisType === 'detailed' && <><IconChartBar size={16} /> Analyse détaillée</>}
            </h3>
            <div
              className="yt-analysis-content message-text"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(analysis || 'Génération en cours...') }}
            />
            {streaming && <div className="yt-streaming-indicator"><span className="spinner" /> Analyse en cours...</div>}
            <div ref={analysisEndRef} />
          </div>
        )}

        {/* Full transcript */}
        {transcript?.full_text && mode === 'transcript' && (
          <div className="yt-transcript-card">
            <div className="yt-transcript-header">
              <h3><IconDocumentText size={16} /> Transcription complète</h3>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => navigator.clipboard.writeText(transcript.full_text)}
              >
                <IconClipboard /> Copier
              </button>
            </div>
            <div className="yt-transcript-text">
              {transcript.full_text}
            </div>
          </div>
        )}

        {/* Index result */}
        {indexResult && (
          <div className="yt-index-result">
            {indexResult.indexed > 0 ? (
              <>
                <div className="yt-success-icon"><IconCheckCircle size={40} /></div>
                <h3>Indexation réussie !</h3>
                <div className="yt-index-stats">
                  <div className="yt-stat">
                    <span className="yt-stat-value">{indexResult.indexed}</span>
                    <span className="yt-stat-label">chunks indexés</span>
                  </div>
                  <div className="yt-stat">
                    <span className="yt-stat-value">{indexResult.subject}</span>
                    <span className="yt-stat-label">matière</span>
                  </div>
                  <div className="yt-stat">
                    <span className="yt-stat-value">{indexResult.language}</span>
                    <span className="yt-stat-label">langue</span>
                  </div>
                  <div className="yt-stat">
                    <span className="yt-stat-value">{(indexResult.text_length || 0).toLocaleString()}</span>
                    <span className="yt-stat-label">caractères</span>
                  </div>
                </div>
                <p className="yt-index-hint">
                  La transcription est maintenant disponible dans le chat RAG pour la matière <strong>{indexResult.subject}</strong>.
                </p>
              </>
            ) : (
              <>
                <div className="yt-warning-icon"><IconAlertTriangle size={40} /></div>
                <h3>Aucun contenu indexé</h3>
                <p>{indexResult.message || 'La transcription est trop courte ou vide.'}</p>
              </>
            )}
          </div>
        )}

        {/* History grid */}
        {mode === 'history' && (
          <div className="yt-history-section">
            {historyLoading ? (
              <div className="yt-history-loading">
                <span className="spinner" />
                <p>Chargement de l'historique...</p>
              </div>
            ) : filteredHistory.length === 0 ? (
              <div className="yt-history-empty">
                <div className="yt-empty-icon"><IconInbox size={48} /></div>
                <h3>{history.length === 0 ? 'Aucune vidéo indexée' : 'Aucun résultat'}</h3>
                <p>
                  {history.length === 0
                    ? 'Indexez des vidéos YouTube via l\'onglet "Indexer" pour les retrouver ici.'
                    : 'Essayez un autre filtre ou terme de recherche.'}
                </p>
              </div>
            ) : (
              <>
                <div className="yt-history-header">
                  <span className="yt-history-count">
                    {filteredHistory.length} vidéo{filteredHistory.length > 1 ? 's' : ''} indexée{filteredHistory.length > 1 ? 's' : ''}
                  </span>
                </div>
                <div className="yt-history-grid">
                  {filteredHistory.map(video => (
                    <div key={video.video_id} className="yt-history-card">
                      <a
                        href={`https://www.youtube.com/watch?v=${video.video_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="yt-history-thumb-link"
                      >
                        <div className="yt-history-thumb">
                          <img
                            src={video.thumbnail || `https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`}
                            alt={video.title || video.video_id}
                            loading="lazy"
                          />
                          <div className="yt-history-play"><IconPlay size={20} /></div>
                          {video.duration && (
                            <span className="yt-history-duration">{formatDuration(video.duration)}</span>
                          )}
                        </div>
                      </a>
                      <div className="yt-history-info">
                        <h4 className="yt-history-title">
                          {video.title || video.video_id}
                        </h4>
                        <div className="yt-history-tags">
                          {video.subject && (
                            <span className="yt-tag yt-tag-subject">{video.subject}</span>
                          )}
                          {video.doc_type && (
                            <span className="yt-tag yt-tag-doctype">{video.doc_type}</span>
                          )}
                          {video.language && (
                            <span className="yt-tag yt-tag-lang">{video.language}</span>
                          )}
                        </div>
                        <div className="yt-history-meta">
                          <span title="Chunks dans ChromaDB">
                            <IconCube /> {video.chunks_count || 0} chunks
                          </span>
                          {video.indexed_at && (
                            <span title="Date d'indexation">
                              <IconCalendar /> {new Date(video.indexed_at).toLocaleDateString('fr-FR')}
                            </span>
                          )}
                        </div>
                        <div className="yt-history-actions">
                          <a
                            href={`https://www.youtube.com/watch?v=${video.video_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary btn-sm"
                          >
                            <IconPlay size={13} /> YouTube
                          </a>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => handleDelete(video.video_id)}
                            disabled={deletingId === video.video_id}
                          >
                            {deletingId === video.video_id
                              ? <span className="spinner" />
                              : <><IconTrash /> Supprimer</>}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Empty state */}
      {mode !== 'history' && !transcript && !analysis && !indexResult && !error && !loading && (
        <div className="yt-empty">
          <div className="yt-empty-icon"><IconFilm /></div>
          <h3>Collez un lien YouTube pour commencer</h3>
          <p>
            <strong>Analyser</strong> : obtenez un résumé IA, les concepts clés, ou une analyse détaillée<br />
            <strong>Indexer</strong> : enrichissez votre base ChromaDB avec le contenu de la vidéo<br />
            <strong>Transcrire</strong> : récupérez la transcription brute
          </p>
          <div className="yt-example-urls">
            <p className="yt-example-label">Exemples :</p>
            <button
              className="yt-example-btn"
              onClick={() => setUrl('https://www.youtube.com/watch?v=aircAruvnKk')}
            >
              Neural Networks — 3Blue1Brown
            </button>
            <button
              className="yt-example-btn"
              onClick={() => setUrl('https://www.youtube.com/watch?v=HGOBQPFzWKo')}
            >
              Intro to Algorithms
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
