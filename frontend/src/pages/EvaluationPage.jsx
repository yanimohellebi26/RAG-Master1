/**
 * EvaluationPage -- Full-page evaluation dashboard.
 *
 * Route: /evaluation
 * Replaces the old in-page modal with a dedicated page.
 */

import React, { useState, useEffect } from 'react'
import { fetchLatestEval, fetchEvalHistory, runEvaluation } from '../services/api'
import '../app/components/ui/EvaluationModal.css'

export default function EvaluationPage() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    loadLatest()
    loadHistory()
  }, [])

  const loadLatest = async () => {
    try {
      const data = await fetchLatestEval()
      setResults(data)
    } catch {
      // No previous results — that's fine
    }
  }

  const loadHistory = async () => {
    try {
      const data = await fetchEvalHistory()
      setHistory(data)
    } catch (err) {
      console.error('Failed to load eval history:', err)
    }
  }

  const handleRun = async () => {
    setLoading(true)
    try {
      const data = await runEvaluation()
      setResults(data)
      await loadHistory()
    } catch (err) {
      console.error('Evaluation failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const pct = (v) => `${(v * 100).toFixed(0)}%`

  return (
    <div className="eval-page" style={{ padding: '2rem', overflowY: 'auto', flex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 className="gradient-text" style={{ fontSize: '1.5rem' }}>Evaluation du systeme RAG</h2>
        <button className="btn btn-primary" onClick={handleRun} disabled={loading}>
          {loading ? 'Evaluation en cours...' : 'Lancer l\'evaluation'}
        </button>
      </div>

      {loading && (
        <div className="loading-state" style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner spinner-lg" />
          <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>
            Evaluation en cours... Cela peut prendre quelques minutes.
          </p>
        </div>
      )}

      {!loading && results && (
        <>
          {/* Primary metrics */}
          <div className="metrics-grid">
            <div className="metric-card metric-primary">
              <div className="metric-label">Score Global</div>
              <div className="metric-value">{pct(results.overall_score)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Fidelite</div>
              <div className="metric-value">{pct(results.avg_faithfulness)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Pertinence</div>
              <div className="metric-value">{pct(results.avg_relevance)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Completude</div>
              <div className="metric-value">{pct(results.avg_completeness)}</div>
            </div>
          </div>

          {/* Secondary metrics */}
          <div className="secondary-metrics" style={{ marginTop: '1rem' }}>
            <div className="metric-item">
              <span>Similarite semantique</span>
              <span>{pct(results.avg_semantic_similarity || 0)}</span>
            </div>
            <div className="metric-item">
              <span>Mots-cles (reponse)</span>
              <span>{pct(results.avg_keyword_coverage)}</span>
            </div>
            <div className="metric-item">
              <span>Match matiere</span>
              <span>{pct(results.avg_subject_match)}</span>
            </div>
            <div className="metric-item">
              <span>Latence moyenne</span>
              <span>{results.avg_latency.toFixed(1)}s</span>
            </div>
          </div>

          {/* Per-question results */}
          {results.results?.length > 0 && (
            <div className="eval-results-section" style={{ marginTop: '2rem' }}>
              <h3>Detail par question</h3>
              <div className="results-list">
                {results.results.map((r, i) => {
                  const avg = (r.answer.faithfulness_score + r.answer.relevance_score + r.answer.completeness_score) / 3
                  const iconColor = avg >= 0.7 ? '#22c55e' : avg >= 0.4 ? '#f59e0b' : '#ef4444'
                  const iconPath = avg >= 0.7
                    ? 'M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4L12 14.01l-3-3'
                    : avg >= 0.4
                    ? 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01'
                    : 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM15 9l-6 6M9 9l6 6'
                  const icon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: 'middle', marginRight: '0.3rem' }}><path d={iconPath}/></svg>
                  return (
                    <details key={i} className="result-item">
                      <summary>
                        {icon} Q{i + 1}. {r.question.slice(0, 80)}... — {pct(avg)}
                      </summary>
                      <div className="result-details">
                        <div className="result-metrics-row">
                          <div className="metric-sm"><span>Fidelite</span><strong>{pct(r.answer.faithfulness_score)}</strong></div>
                          <div className="metric-sm"><span>Pertinence</span><strong>{pct(r.answer.relevance_score)}</strong></div>
                          <div className="metric-sm"><span>Completude</span><strong>{pct(r.answer.completeness_score)}</strong></div>
                          <div className="metric-sm"><span>Latence</span><strong>{r.latency_seconds.toFixed(1)}s</strong></div>
                        </div>
                        <div className="result-text">
                          <strong>Reponse attendue :</strong>
                          <p className="expected-answer">{r.expected_answer}</p>
                          <strong>Reponse generee :</strong>
                          <p className="generated-answer">{r.generated_answer.slice(0, 500)}</p>
                        </div>
                      </div>
                    </details>
                  )
                })}
              </div>
            </div>
          )}

          {/* History */}
          {history.length >= 2 && (
            <div className="eval-history-section" style={{ marginTop: '2rem' }}>
              <h3>Historique</h3>
              <div className="history-list">
                {history.slice(0, 10).map((h, i) => (
                  <div key={i} className="history-item">
                    <span className="history-date">{h.timestamp?.slice(0, 19).replace('T', ' ')}</span>
                    <span className="history-score">{pct(h.overall_score)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!loading && !results && (
        <div className="empty-state">
          <div className="empty-state-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div>
          <div className="empty-state-title">Aucune evaluation disponible</div>
          <p className="empty-state-text">
            Lancez une evaluation pour mesurer la qualite du systeme RAG.
          </p>
        </div>
      )}
    </div>
  )
}
