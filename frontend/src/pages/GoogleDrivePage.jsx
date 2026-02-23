/**
 * GoogleDrivePage -- Page dediee a la synchronisation de fichiers Google Drive.
 *
 * Permet de :
 *   1. Connecter le service account Google Drive
 *   2. Parcourir les fichiers d'un dossier
 *   3. Synchroniser tout un dossier ou une selection vers ChromaDB
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

const MIME_ICONS = {
  'application/pdf': '📄',
  'application/vnd.google-apps.document': '📝',
  'application/vnd.google-apps.presentation': '📊',
  'application/vnd.google-apps.spreadsheet': '📈',
  'application/vnd.google-apps.folder': '📁',
  'text/plain': '📃',
  'text/csv': '📋',
}

function getFileIcon(mimeType) {
  return MIME_ICONS[mimeType] || '📎'
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

  const toggleSelectAll = () => {
    const syncable = files.filter((f) => f.mimeType !== 'application/vnd.google-apps.folder')
    if (selectedIds.size === syncable.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(syncable.map((f) => f.id)))
    }
  }

  const handleSync = async (mode) => {
    if (!subject) {
      setError('Veuillez choisir une matiere')
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

  const isConnected = status?.connected

  return (
    <div className="gdrive-page">
      {/* Header */}
      <div className="gd-header">
        <div className="gd-header-icon">📂</div>
        <div>
          <h2 className="gradient-text">Google Drive</h2>
          <p className="gd-header-subtitle">
            Synchronisez vos documents partages (PDF, Slides, Docs) vers ChromaDB
          </p>
        </div>
        {status && (
          <span className={`badge ${isConnected ? 'badge-success' : 'badge-error'}`}>
            {isConnected ? 'Connecte' : 'Non connecte'}
          </span>
        )}
      </div>

      {/* Connection section */}
      {!isConnected && (
        <div className="gd-connect-section">
          <p className="gd-connect-info">
            {status?.message || 'Chargement...'}
          </p>
          {status?.available && (
            <button
              className="btn btn-primary"
              onClick={handleConnect}
              disabled={connecting}
            >
              {connecting ? (
                <>
                  <span className="spinner" /> Connexion...
                </>
              ) : (
                '🔗 Connecter Google Drive'
              )}
            </button>
          )}
        </div>
      )}

      {/* Main content (only when connected) */}
      {isConnected && (
        <>
          {/* Folder input + subject */}
          <div className="gd-controls">
            <div className="gd-controls-row">
              <div className="gd-input-group gd-folder-group">
                <label>Dossier Drive (Folder ID)</label>
                <div className="gd-folder-input-row">
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
                    className="btn btn-primary"
                    onClick={handleLoadFiles}
                    disabled={!folderId.trim() || loading}
                  >
                    {loading ? (
                      <>
                        <span className="spinner" /> Chargement...
                      </>
                    ) : (
                      '📂 Charger les fichiers'
                    )}
                  </button>
                </div>
              </div>
              <div className="gd-input-group">
                <label>Matiere *</label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="select-input"
                >
                  <option value="">-- Choisir une matiere --</option>
                  {subjects.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="gd-files-section">
              <div className="gd-files-header">
                <div className="gd-files-header-left">
                  <label className="gd-checkbox-label">
                    <input
                      type="checkbox"
                      checked={
                        selectedIds.size > 0 &&
                        selectedIds.size ===
                          files.filter((f) => f.mimeType !== 'application/vnd.google-apps.folder')
                            .length
                      }
                      onChange={toggleSelectAll}
                    />
                    <span>Tout selectionner</span>
                  </label>
                  <span className="gd-files-count">
                    {files.length} fichier{files.length > 1 ? 's' : ''}
                    {selectedIds.size > 0 && ` (${selectedIds.size} selectionne${selectedIds.size > 1 ? 's' : ''})`}
                  </span>
                </div>
                <div className="gd-files-header-right">
                  {selectedIds.size > 0 && (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleSync('selected')}
                      disabled={syncing || !subject}
                    >
                      {syncing ? (
                        <>
                          <span className="spinner" /> Sync...
                        </>
                      ) : (
                        `📥 Synchroniser la selection (${selectedIds.size})`
                      )}
                    </button>
                  )}
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleSync('all')}
                    disabled={syncing || !subject}
                  >
                    {syncing ? (
                      <>
                        <span className="spinner" /> Sync...
                      </>
                    ) : (
                      '📥 Synchroniser tout le dossier'
                    )}
                  </button>
                </div>
              </div>

              <div className="gd-files-list">
                {files.map((file) => {
                  const isFolder = file.mimeType === 'application/vnd.google-apps.folder'
                  return (
                    <div
                      key={file.id}
                      className={`gd-file-row ${selectedIds.has(file.id) ? 'selected' : ''}`}
                    >
                      {!isFolder && (
                        <input
                          type="checkbox"
                          checked={selectedIds.has(file.id)}
                          onChange={() => toggleSelect(file.id)}
                        />
                      )}
                      {isFolder && <span className="gd-file-checkbox-spacer" />}
                      <span className="gd-file-icon">{getFileIcon(file.mimeType)}</span>
                      <div className="gd-file-info">
                        <span className="gd-file-name">{file.name}</span>
                        <span className="gd-file-meta">
                          {file.type_label}
                          {file.size > 0 && ` · ${formatSize(file.size)}`}
                          {file.modifiedTime &&
                            ` · ${new Date(file.modifiedTime).toLocaleDateString('fr-FR')}`}
                        </span>
                      </div>
                      <div className="gd-file-actions">
                        {!isFolder && (
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => handlePreview(file.id)}
                            disabled={previewLoading}
                          >
                            👁 Apercu
                          </button>
                        )}
                        {file.webViewLink && (
                          <a
                            href={file.webViewLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-ghost btn-sm"
                          >
                            🔗 Ouvrir
                          </a>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Preview panel */}
          {preview && (
            <div className="gd-preview">
              <div className="gd-preview-header">
                <h3>
                  {getFileIcon(preview.mimeType)} {preview.name}
                </h3>
                <button className="btn btn-ghost btn-sm" onClick={() => setPreview(null)}>
                  Fermer
                </button>
              </div>
              <div className="gd-preview-meta">
                <span>Type : {preview.mimeType}</span>
                <span>{preview.content_length?.toLocaleString()} caracteres</span>
                {preview.truncated && <span className="gd-preview-truncated">Apercu tronque</span>}
              </div>
              <pre className="gd-preview-content">{preview.preview}</pre>
            </div>
          )}
        </>
      )}

      {/* Error */}
      {error && (
        <div className="gd-error">
          <span>❌</span>
          <p>{error}</p>
          <button className="btn btn-ghost btn-sm" onClick={() => setError('')}>
            Fermer
          </button>
        </div>
      )}

      {/* Sync result */}
      {syncResult && (
        <div className="gd-sync-result">
          {syncResult.total_chunks > 0 ? (
            <>
              <div className="gd-success-icon">✅</div>
              <h3>Synchronisation reussie !</h3>
              <div className="gd-sync-stats">
                <div className="gd-stat">
                  <span className="gd-stat-value">{syncResult.synced_files}</span>
                  <span className="gd-stat-label">fichiers synchronises</span>
                </div>
                <div className="gd-stat">
                  <span className="gd-stat-value">{syncResult.total_chunks}</span>
                  <span className="gd-stat-label">chunks indexes</span>
                </div>
                <div className="gd-stat">
                  <span className="gd-stat-value">{syncResult.subject}</span>
                  <span className="gd-stat-label">matiere</span>
                </div>
              </div>
              <p className="gd-sync-hint">
                Les documents sont maintenant disponibles dans le chat RAG pour la matiere{' '}
                <strong>{syncResult.subject}</strong>.
              </p>
            </>
          ) : (
            <>
              <div className="gd-warning-icon">⚠️</div>
              <h3>Aucun contenu indexe</h3>
              <p>Aucun fichier exploitable trouve dans ce dossier.</p>
            </>
          )}
        </div>
      )}

      {/* Empty state */}
      {isConnected && files.length === 0 && !loading && !error && !syncResult && (
        <div className="gd-empty">
          <div className="gd-empty-icon">📂</div>
          <h3>Entrez un Folder ID pour parcourir vos fichiers</h3>
          <p>
            Vous trouverez le Folder ID dans l'URL de Google Drive :
            <br />
            <code>drive.google.com/drive/folders/<strong>FOLDER_ID</strong></code>
          </p>
        </div>
      )}
    </div>
  )
}
