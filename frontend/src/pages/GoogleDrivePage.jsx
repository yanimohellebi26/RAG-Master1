/**
 * GoogleDrivePage -- Synchronisation de fichiers Google Drive vers ChromaDB.
 *
 * Interface fluide avec :
 *   - Connexion au service account
 *   - Navigation dans les dossiers Drive
 *   - Selection de fichiers avec apercu
 *   - Synchronisation vers ChromaDB avec progression
 */

import React, { useState, useEffect, useCallback } from 'react'
import { useApp } from '../contexts/AppContext'
import {
  fetchGDriveStatus,
  connectGDrive,
  fetchGDriveFiles,
  previewGDriveFile,
  syncGDriveFolder,
} from '../services/api'
import './GoogleDrivePage.css'

const FILE_TYPE_CONFIG = {
  'application/pdf':                                         { icon: '📄', label: 'PDF',    color: '#ef4444' },
  'application/vnd.google-apps.document':                    { icon: '📝', label: 'Doc',    color: '#3b82f6' },
  'application/vnd.google-apps.presentation':                { icon: '📊', label: 'Slides', color: '#f59e0b' },
  'application/vnd.google-apps.spreadsheet':                 { icon: '📈', label: 'Sheet',  color: '#22c55e' },
  'application/vnd.google-apps.folder':                      { icon: '📁', label: 'Dossier',color: '#8b5cf6' },
  'text/plain':                                              { icon: '📃', label: 'TXT',    color: '#6b7280' },
  'text/csv':                                                { icon: '📋', label: 'CSV',    color: '#14b8a6' },
}

function getFileConfig(mimeType) {
  return FILE_TYPE_CONFIG[mimeType] || { icon: '📎', label: 'Fichier', color: '#6b7280' }
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function GoogleDrivePage() {
  const { config } = useApp()

  const [status, setStatus] = useState(null)
  const [connecting, setConnecting] = useState(false)
  const [folderId, setFolderId] = useState('')
  const [files, setFiles] = useState([])
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [subject, setSubject] = useState('')
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState(null)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const subjects = config?.subjects || []

  // Load status on mount
  useEffect(() => {
    fetchGDriveStatus()
      .then((s) => {
        setStatus(s)
        if (s.default_folder_id) setFolderId(s.default_folder_id)
      })
      .catch(() => setStatus({ available: false }))
  }, [])

  const handleConnect = async () => {
    setConnecting(true)
    setError('')
    try {
      const result = await connectGDrive()
      setStatus((prev) => ({ ...prev, connected: result.connected }))
      if (!result.connected) setError(result.message || 'Connexion echouee')
    } catch (err) {
      setError(err.message)
    } finally {
      setConnecting(false)
    }
  }

  const handleLoadFiles = useCallback(async () => {
    if (!folderId.trim()) return
    setLoading(true)
    setError('')
    setFiles([])
    setSelectedIds(new Set())
    setSyncResult(null)
    setPreview(null)
    try {
      const data = await fetchGDriveFiles(folderId.trim())
      setFiles(data.files || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [folderId])

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const syncableFiles = files.filter((f) => f.mimeType !== 'application/vnd.google-apps.folder')

  const toggleSelectAll = () => {
    if (selectedIds.size === syncableFiles.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(syncableFiles.map((f) => f.id)))
    }
  }

  const handleSync = async (mode) => {
    if (!subject) {
      setError('Veuillez choisir une matiere avant de synchroniser')
      return
    }
    setSyncing(true)
    setError('')
    setSyncResult(null)
    try {
      const payload = { subject }
      if (mode === 'selected') {
        payload.file_ids = [...selectedIds]
      } else {
        payload.folder_id = folderId.trim()
      }
      const result = await syncGDriveFolder(payload)
      setSyncResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setSyncing(false)
    }
  }

  const handlePreview = async (fileId) => {
    if (preview?.id === fileId) {
      setPreview(null)
      return
    }
    setPreviewLoading(true)
    try {
      const data = await previewGDriveFile(fileId)
      setPreview(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setPreviewLoading(false)
    }
  }

  // Filter files by search
  const filteredFiles = files.filter((f) => {
    if (!searchQuery) return true
    return f.name.toLowerCase().includes(searchQuery.toLowerCase())
  })

  const isConnected = status?.connected

  // Count by type for the summary bar
  const typeCounts = files.reduce((acc, f) => {
    const cfg = getFileConfig(f.mimeType)
    acc[cfg.label] = (acc[cfg.label] || 0) + 1
    return acc
  }, {})

  return (
    <div className="gdrive-page">
      {/* ── Header ── */}
      <div className="gd-header animate-fade-in">
        <div className="gd-header-icon-wrap">
          <div className="gd-header-icon">
            <svg viewBox="0 0 87.3 78" width="36" height="32">
              <path d="M6.6 66.85l3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8H0c0 1.55.4 3.1 1.2 4.5l5.4 9.35z" fill="#0066da"/>
              <path d="M43.65 25L29.9 1.2C28.55 2 27.4 3.1 26.6 4.5L1.2 48.55C.4 49.95 0 51.5 0 53h27.5L43.65 25z" fill="#00ac47"/>
              <path d="M73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75L84.7 58.5c.8-1.4 1.2-2.95 1.2-4.5H59.8l5.95 11.35 7.8 11.45z" fill="#ea4335"/>
              <path d="M43.65 25L57.4 1.2c-1.35-.8-2.9-1.2-4.5-1.2H34.35c-1.6 0-3.15.45-4.5 1.2L43.65 25z" fill="#00832d"/>
              <path d="M59.8 53h-32.3L13.75 76.8c1.35.8 2.9 1.2 4.5 1.2h36.85c1.6 0 3.15-.45 4.5-1.2L59.8 53z" fill="#2684fc"/>
              <path d="M73.4 26.5l-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3L43.65 25l16.15 28h27.45c0-1.55-.4-3.1-1.2-4.5l-12.65-22z" fill="#ffba00"/>
            </svg>
          </div>
        </div>
        <div className="gd-header-text">
          <h2 className="gradient-text">Google Drive</h2>
          <p className="gd-header-subtitle">
            Synchronisez vos documents partages vers ChromaDB pour les utiliser dans le chat RAG
          </p>
        </div>
        <div className="gd-header-status">
          {status && (
            <span className={`gd-status-pill ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="gd-status-dot" />
              {isConnected ? 'Connecte' : 'Non connecte'}
            </span>
          )}
        </div>
      </div>

      {/* ── Connection card ── */}
      {!isConnected && (
        <div className="gd-connect-card animate-fade-in">
          <div className="gd-connect-visual">
            <div className="gd-connect-circles">
              <div className="gd-circle gd-circle-1" />
              <div className="gd-circle gd-circle-2" />
              <div className="gd-circle gd-circle-3" />
            </div>
            <div className="gd-connect-icon-large">
              <svg viewBox="0 0 87.3 78" width="64" height="58">
                <path d="M6.6 66.85l3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8H0c0 1.55.4 3.1 1.2 4.5l5.4 9.35z" fill="#0066da"/>
                <path d="M43.65 25L29.9 1.2C28.55 2 27.4 3.1 26.6 4.5L1.2 48.55C.4 49.95 0 51.5 0 53h27.5L43.65 25z" fill="#00ac47"/>
                <path d="M73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75L84.7 58.5c.8-1.4 1.2-2.95 1.2-4.5H59.8l5.95 11.35 7.8 11.45z" fill="#ea4335"/>
                <path d="M43.65 25L57.4 1.2c-1.35-.8-2.9-1.2-4.5-1.2H34.35c-1.6 0-3.15.45-4.5 1.2L43.65 25z" fill="#00832d"/>
                <path d="M59.8 53h-32.3L13.75 76.8c1.35.8 2.9 1.2 4.5 1.2h36.85c1.6 0 3.15-.45 4.5-1.2L59.8 53z" fill="#2684fc"/>
                <path d="M73.4 26.5l-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3L43.65 25l16.15 28h27.45c0-1.55-.4-3.1-1.2-4.5l-12.65-22z" fill="#ffba00"/>
              </svg>
            </div>
          </div>
          <h3>Connecter Google Drive</h3>
          <p className="gd-connect-desc">
            {status?.message || 'Chargement du statut...'}
          </p>
          {status?.available && (
            <button
              className="btn btn-primary gd-connect-btn"
              onClick={handleConnect}
              disabled={connecting}
            >
              {connecting ? (
                <><span className="spinner" /> Connexion en cours...</>
              ) : (
                'Connecter le service'
              )}
            </button>
          )}
          <div className="gd-connect-hint">
            <span className="gd-hint-icon">i</span>
            Placez votre fichier <code>service_account.json</code> dans <code>credentials/</code> et activez dans <code>config.yaml</code>
          </div>
        </div>
      )}

      {/* ── Error banner ── */}
      {error && (
        <div className="gd-error animate-fade-in">
          <div className="gd-error-icon">!</div>
          <p>{error}</p>
          <button className="gd-error-close" onClick={() => setError('')}>
            &times;
          </button>
        </div>
      )}

      {/* ── Main content ── */}
      {isConnected && (
        <>
          {/* Controls bar */}
          <div className="gd-controls animate-fade-in">
            <div className="gd-controls-main">
              <div className="gd-folder-input-wrap">
                <span className="gd-folder-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                  </svg>
                </span>
                <input
                  type="text"
                  className="gd-folder-input"
                  placeholder="Collez l'ID du dossier Google Drive..."
                  value={folderId}
                  onChange={(e) => setFolderId(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleLoadFiles()
                  }}
                  disabled={loading}
                />
                <button
                  className="gd-load-btn"
                  onClick={handleLoadFiles}
                  disabled={!folderId.trim() || loading}
                >
                  {loading ? (
                    <span className="spinner" />
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="23 4 23 10 17 10"/>
                      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                    </svg>
                  )}
                  {loading ? 'Chargement...' : 'Charger'}
                </button>
              </div>
              <div className="gd-subject-wrap">
                <label>Matiere</label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="gd-subject-select"
                >
                  <option value="">-- Choisir --</option>
                  {subjects.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Sync progress overlay */}
          {syncing && (
            <div className="gd-sync-progress animate-fade-in">
              <div className="gd-sync-progress-bar">
                <div className="gd-sync-progress-fill" />
              </div>
              <div className="gd-sync-progress-text">
                <span className="spinner" />
                Synchronisation en cours... Extraction et indexation des documents
              </div>
            </div>
          )}

          {/* File list */}
          {files.length > 0 && !syncing && (
            <div className="gd-files-card animate-fade-in">
              {/* Toolbar */}
              <div className="gd-toolbar">
                <div className="gd-toolbar-left">
                  <label className="gd-select-all">
                    <input
                      type="checkbox"
                      checked={selectedIds.size > 0 && selectedIds.size === syncableFiles.length}
                      onChange={toggleSelectAll}
                    />
                    <span className="gd-custom-checkbox" />
                  </label>
                  <span className="gd-file-count">
                    {files.length} fichier{files.length > 1 ? 's' : ''}
                  </span>
                  {selectedIds.size > 0 && (
                    <span className="gd-selected-badge">
                      {selectedIds.size} selectionne{selectedIds.size > 1 ? 's' : ''}
                    </span>
                  )}
                  <div className="gd-type-tags">
                    {Object.entries(typeCounts).map(([label, count]) => {
                      const cfg = Object.values(FILE_TYPE_CONFIG).find(c => c.label === label)
                      return (
                        <span
                          key={label}
                          className="gd-type-tag"
                          style={{ '--tag-color': cfg?.color || '#6b7280' }}
                        >
                          {count} {label}
                        </span>
                      )
                    })}
                  </div>
                </div>
                <div className="gd-toolbar-right">
                  <div className="gd-search-mini">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8"/>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    <input
                      type="text"
                      placeholder="Filtrer..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  {selectedIds.size > 0 && (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleSync('selected')}
                      disabled={syncing || !subject}
                    >
                      Indexer la selection ({selectedIds.size})
                    </button>
                  )}
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleSync('all')}
                    disabled={syncing || !subject}
                  >
                    Indexer tout
                  </button>
                </div>
              </div>

              {/* File rows */}
              <div className="gd-file-list">
                {filteredFiles.map((file, idx) => {
                  const isFolder = file.mimeType === 'application/vnd.google-apps.folder'
                  const cfg = getFileConfig(file.mimeType)
                  const isSelected = selectedIds.has(file.id)
                  const isPreviewed = preview?.id === file.id

                  return (
                    <div
                      key={file.id}
                      className={`gd-file-row ${isSelected ? 'selected' : ''} ${isPreviewed ? 'previewed' : ''}`}
                      style={{ animationDelay: `${idx * 30}ms` }}
                    >
                      <div className="gd-file-check">
                        {!isFolder ? (
                          <label className="gd-file-checkbox-label">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSelect(file.id)}
                            />
                            <span className="gd-custom-checkbox" />
                          </label>
                        ) : (
                          <span className="gd-file-checkbox-spacer" />
                        )}
                      </div>
                      <div
                        className="gd-file-type-badge"
                        style={{ '--badge-color': cfg.color }}
                      >
                        <span className="gd-file-type-icon">{cfg.icon}</span>
                      </div>
                      <div className="gd-file-details">
                        <span className="gd-file-name">{file.name}</span>
                        <div className="gd-file-meta-row">
                          <span
                            className="gd-file-type-label"
                            style={{ color: cfg.color }}
                          >
                            {cfg.label}
                          </span>
                          {file.size > 0 && (
                            <span className="gd-file-size">{formatSize(file.size)}</span>
                          )}
                          {file.modifiedTime && (
                            <span className="gd-file-date">
                              {new Date(file.modifiedTime).toLocaleDateString('fr-FR')}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="gd-file-actions">
                        {!isFolder && (
                          <button
                            className={`gd-action-btn ${isPreviewed ? 'active' : ''}`}
                            onClick={() => handlePreview(file.id)}
                            disabled={previewLoading}
                            title="Apercu du contenu"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                              <circle cx="12" cy="12" r="3"/>
                            </svg>
                          </button>
                        )}
                        {file.webViewLink && (
                          <a
                            href={file.webViewLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="gd-action-btn"
                            title="Ouvrir dans Drive"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                              <polyline points="15 3 21 3 21 9"/>
                              <line x1="10" y1="14" x2="21" y2="3"/>
                            </svg>
                          </a>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {filteredFiles.length === 0 && searchQuery && (
                <div className="gd-no-results">
                  Aucun fichier ne correspond a &laquo; {searchQuery} &raquo;
                </div>
              )}
            </div>
          )}

          {/* Preview panel */}
          {preview && (
            <div className="gd-preview animate-fade-in">
              <div className="gd-preview-header">
                <div className="gd-preview-title">
                  <span className="gd-preview-icon">{getFileConfig(preview.mimeType).icon}</span>
                  <div>
                    <h3>{preview.name}</h3>
                    <div className="gd-preview-badges">
                      <span
                        className="gd-preview-type"
                        style={{ '--badge-color': getFileConfig(preview.mimeType).color }}
                      >
                        {getFileConfig(preview.mimeType).label}
                      </span>
                      <span className="gd-preview-chars">
                        {preview.content_length?.toLocaleString()} caracteres
                      </span>
                      {preview.truncated && (
                        <span className="gd-preview-truncated">Apercu partiel</span>
                      )}
                    </div>
                  </div>
                </div>
                <button className="gd-action-btn" onClick={() => setPreview(null)} title="Fermer">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
              <pre className="gd-preview-content">{preview.preview}</pre>
            </div>
          )}

          {/* Sync result */}
          {syncResult && !syncing && (
            <div className={`gd-result animate-fade-in ${syncResult.total_chunks > 0 ? 'success' : 'empty'}`}>
              {syncResult.total_chunks > 0 ? (
                <>
                  <div className="gd-result-header">
                    <div className="gd-result-check">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                      </svg>
                    </div>
                    <h3>Synchronisation reussie</h3>
                  </div>
                  <div className="gd-result-stats">
                    <div className="gd-result-stat">
                      <span className="gd-result-stat-value">{syncResult.synced_files}</span>
                      <span className="gd-result-stat-label">Fichiers</span>
                    </div>
                    <div className="gd-result-stat-divider" />
                    <div className="gd-result-stat">
                      <span className="gd-result-stat-value">{syncResult.total_chunks}</span>
                      <span className="gd-result-stat-label">Chunks</span>
                    </div>
                    <div className="gd-result-stat-divider" />
                    <div className="gd-result-stat">
                      <span className="gd-result-stat-value gd-result-subject">{syncResult.subject}</span>
                      <span className="gd-result-stat-label">Matiere</span>
                    </div>
                  </div>
                  <p className="gd-result-hint">
                    Les documents sont indexes et disponibles dans le chat RAG.
                  </p>
                </>
              ) : (
                <>
                  <div className="gd-result-header">
                    <div className="gd-result-warn">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                        <line x1="12" y1="9" x2="12" y2="13"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                    </div>
                    <h3>Aucun contenu indexe</h3>
                  </div>
                  <p className="gd-result-hint">
                    Aucun fichier exploitable n'a ete trouve. Verifiez que le dossier contient des documents supportes (PDF, Docs, Slides, TXT).
                  </p>
                </>
              )}
            </div>
          )}

          {/* Empty state */}
          {files.length === 0 && !loading && !error && !syncResult && !syncing && (
            <div className="gd-empty animate-fade-in">
              <div className="gd-empty-illustration">
                <div className="gd-empty-folder">
                  <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                  </svg>
                </div>
              </div>
              <h3>Parcourez vos fichiers Drive</h3>
              <p>
                Entrez l'identifiant d'un dossier Google Drive pour lister et synchroniser vos documents.
              </p>
              <div className="gd-empty-help">
                <div className="gd-help-step">
                  <span className="gd-step-num">1</span>
                  <span>Ouvrez un dossier dans Google Drive</span>
                </div>
                <div className="gd-help-step">
                  <span className="gd-step-num">2</span>
                  <span>Copiez l'ID depuis l'URL : <code>drive.google.com/drive/folders/<strong>ID</strong></code></span>
                </div>
                <div className="gd-help-step">
                  <span className="gd-step-num">3</span>
                  <span>Collez-le ci-dessus et chargez les fichiers</span>
                </div>
              </div>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="gd-loading animate-fade-in">
              <div className="gd-loading-spinner">
                <span className="spinner spinner-lg" />
              </div>
              <p>Chargement des fichiers du dossier...</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
