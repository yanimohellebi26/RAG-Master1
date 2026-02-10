/**
 * YouTubePage -- Page dediee a l'analyse de videos YouTube.
 *
 * Deux modes :
 *   1. Analyse : coller un lien → transcription + resume/concepts/analyse IA (streaming)
 *   2. Indexation : coller un lien + choisir matiere → indexer dans ChromaDB
 */

import React, { useState, useRef, useEffect } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useApp } from '../contexts/AppContext'
import {
  fetchYouTubeStatus,
  fetchYouTubeTranscript,
  indexYouTubeTranscript,
  analyzeYouTubeStream,
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

export default function YouTubePage() {
  const { config } = useApp()

  const [url, setUrl] = useState('')
  const [mode, setMode] = useState('analyze') // 'analyze' | 'index'
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
        <div className="yt-header-icon">🎬</div>
        <div>
          <h2 className="gradient-text">YouTube Transcript</h2>
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
            <span className="yt-url-icon">▶</span>
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
            🔍 Analyser
          </button>
          <button
            className={`yt-mode-tab ${mode === 'index' ? 'active' : ''}`}
            onClick={() => setMode('index')}
          >
            📥 Indexer dans ChromaDB
          </button>
          <button
            className={`yt-mode-tab ${mode === 'transcript' ? 'active' : ''}`}
            onClick={() => setMode('transcript')}
          >
            📝 Transcription brute
          </button>
        </div>

        {/* Mode-specific options */}
        {mode === 'analyze' && (
          <div className="yt-options">
            <div className="yt-option-group">
              <label>Type d'analyse</label>
              <div className="yt-analysis-chips">
                {[
                  { id: 'summary', label: '📋 Résumé', desc: 'Résumé structuré' },
                  { id: 'concepts', label: '💡 Concepts', desc: 'Concepts clés' },
                  { id: 'detailed', label: '📊 Détaillée', desc: 'Analyse complète' },
                ].map(opt => (
                  <button
                    key={opt.id}
                    className={`yt-chip ${analysisType === opt.id ? 'active' : ''}`}
                    onClick={() => setAnalysisType(opt.id)}
                  >
                    {opt.label}
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
              {loading ? <><span className="spinner" /> Analyse en cours...</> : '🚀 Analyser la vidéo'}
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
              {loading ? <><span className="spinner" /> Indexation en cours...</> : '📥 Indexer dans ChromaDB'}
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
              {loading ? <><span className="spinner" /> Récupération...</> : '📝 Récupérer la transcription'}
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="yt-error">
          <span>❌</span>
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
                ▶ Voir la vidéo sur YouTube
              </a>
            )}
          </div>
        )}

        {/* Streaming analysis */}
        {(analysis || streaming) && (
          <div className="yt-analysis-card">
            <h3>
              {analysisType === 'summary' && '📋 Résumé'}
              {analysisType === 'concepts' && '💡 Concepts clés'}
              {analysisType === 'detailed' && '📊 Analyse détaillée'}
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
              <h3>📝 Transcription complète</h3>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => navigator.clipboard.writeText(transcript.full_text)}
              >
                📋 Copier
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
                <div className="yt-success-icon">✅</div>
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
                <div className="yt-warning-icon">⚠️</div>
                <h3>Aucun contenu indexé</h3>
                <p>{indexResult.message || 'La transcription est trop courte ou vide.'}</p>
              </>
            )}
          </div>
        )}
      </div>

      {/* Empty state */}
      {!transcript && !analysis && !indexResult && !error && !loading && (
        <div className="yt-empty">
          <div className="yt-empty-icon">🎬</div>
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
