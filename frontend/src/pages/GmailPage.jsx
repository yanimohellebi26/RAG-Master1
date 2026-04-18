/**
 * GmailPage -- Lecture et redaction de mails via Gmail.
 *
 * Deux sections :
 *   - Mails non lus : liste, detail, resume LLM, auto-classification, statuts
 *   - Rediger : formulaire d'envoi avec assistance LLM
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  fetchGmailStatus,
  connectGmail,
  fetchGmailUnread,
  fetchGmailEmail,
  summarizeGmailUnread,
  draftGmailReply,
  sendGmailEmail,
  fetchGmailCategories,
  categorizeGmailEmail,
  uncategorizeGmailEmail,
  setGmailEmailStatus,
} from '../services/api'
import './GmailPage.css'

/* -- SVG Icon components -------------------------------------------------- */

function IconMail() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <rect x="2" y="4" width="20" height="16" rx="2" stroke="#ea4335" strokeWidth="1.5" fill="rgba(234,67,53,0.08)" />
      <path d="M2 6l10 7 10-7" stroke="#ea4335" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  )
}

function IconInbox() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  )
}

function IconEdit() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconSend() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <line x1="22" y1="2" x2="11" y2="13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  )
}

function IconSpark() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <path d="M12 2L9 12l-7 1 7 1 3 10 3-10 7-1-7-1L12 2z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  )
}

function IconAttachment() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconFile() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <polyline points="14 2 14 8 20 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconDownload() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="7 10 12 15 17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconClose() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
      <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function IconBack() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <line x1="19" y1="12" x2="5" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <polyline points="12 19 5 12 12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  )
}

function IconRefresh() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <polyline points="23 4 23 10 17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  )
}

/* -- Statuses config ------------------------------------------------------ */

const STATUS_LIST = ['Nouveau', 'En cours', 'Traite']
const STATUS_COLORS = {
  'Nouveau': '#3b82f6',
  'En cours': '#f59e0b',
  'Traite': '#22c55e',
}

/* -- Component ------------------------------------------------------------ */

export default function GmailPage() {
  // Connection state
  const [status, setStatus] = useState(null)
  const [connecting, setConnecting] = useState(false)

  // Tab: 'inbox' or 'compose'
  const [activeTab, setActiveTab] = useState('inbox')

  // Inbox state
  const [emails, setEmails] = useState([])
  const [loadingEmails, setLoadingEmails] = useState(false)
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  // Selection state (for selective summarize)
  const [selectedUids, setSelectedUids] = useState(new Set())

  // Summary state
  const [summary, setSummary] = useState(null)
  const [summarizing, setSummarizing] = useState(false)

  // Compose state
  const [composeTo, setComposeTo] = useState('')
  const [composeSubject, setComposeSubject] = useState('')
  const [composeBody, setComposeBody] = useState('')
  const [assisting, setAssisting] = useState(false)
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState(null)
  const [composeFiles, setComposeFiles] = useState([])
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = React.useRef(null)

  // Date filter (default: month)
  const [dateFilter, setDateFilter] = useState('month')

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [totalEmails, setTotalEmails] = useState(0)

  // Categories
  const [categories, setCategories] = useState({})
  const [categoryFilter, setCategoryFilter] = useState(null)
  const [globalCategoryCounts, setGlobalCategoryCounts] = useState({})

  // Error
  const [error, setError] = useState(null)

  // -- Load status on mount
  useEffect(() => {
    fetchGmailStatus()
      .then(setStatus)
      .catch((err) => setError(err.message))
  }, [])

  // -- Connect
  const handleConnect = useCallback(async () => {
    setConnecting(true)
    setError(null)
    try {
      const res = await connectGmail()
      setStatus((prev) => ({ ...prev, connected: res.connected, message: res.message }))
    } catch (err) {
      setError(err.message)
    } finally {
      setConnecting(false)
    }
  }, [])

  // -- Fetch emails (enriched with category + status from backend)
  const handleFetchEmails = useCallback(async (filter, page) => {
    const f = filter ?? dateFilter
    const p = page ?? currentPage
    setLoadingEmails(true)
    setError(null)
    setSummary(null)
    setSelectedEmail(null)
    setSelectedUids(new Set())
    try {
      const res = await fetchGmailUnread({ filter: f, page: p })
      setEmails(res.emails || [])
      setTotalPages(res.total_pages || 0)
      setTotalEmails(res.total || 0)
      setCurrentPage(res.page || 1)
      if (res.category_counts) setGlobalCategoryCounts(res.category_counts)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingEmails(false)
    }
  }, [dateFilter, currentPage])

  // Auto-fetch on connect
  useEffect(() => {
    if (status?.connected) {
      handleFetchEmails('month', 1)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.connected])

  // -- Read single email
  const handleReadEmail = useCallback(async (uid) => {
    setLoadingDetail(true)
    setError(null)
    try {
      const res = await fetchGmailEmail(uid)
      setSelectedEmail(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  // -- Filtered emails (by category) — defined early for use in toggleSelectAll
  const filteredEmails = categoryFilter
    ? emails.filter((em) => em.category === categoryFilter)
    : emails

  // -- Summarize (selective or all)
  const handleSummarize = useCallback(async () => {
    setSummarizing(true)
    setError(null)
    try {
      const payload = selectedUids.size > 0 ? { uids: Array.from(selectedUids) } : {}
      const res = await summarizeGmailUnread(payload)
      setSummary(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setSummarizing(false)
    }
  }, [selectedUids])

  // -- Toggle selection
  const toggleSelectUid = useCallback((uid) => {
    setSelectedUids((prev) => {
      const next = new Set(prev)
      if (next.has(uid)) next.delete(uid)
      else next.add(uid)
      return next
    })
  }, [])

  const toggleSelectAll = useCallback(() => {
    setSelectedUids((prev) => {
      if (prev.size === filteredEmails.length) return new Set()
      return new Set(filteredEmails.map((em) => em.uid))
    })
  }, [filteredEmails])

  // -- Draft reply (assist compose body)
  const handleAssist = useCallback(async () => {
    if (!composeBody.trim()) return
    setAssisting(true)
    setError(null)
    try {
      const payload = { instructions: composeBody }
      if (selectedEmail?.uid) payload.uid = selectedEmail.uid
      const res = await draftGmailReply(payload)
      if (res.draft) {
        setComposeBody(res.draft)
        if (res.to && !composeTo) setComposeTo(res.to)
        if (res.original_subject && !composeSubject) {
          setComposeSubject(`Re: ${res.original_subject}`)
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setAssisting(false)
    }
  }, [composeBody, composeTo, composeSubject, selectedEmail])

  // -- Send email
  const handleSend = useCallback(async () => {
    if (!composeTo.trim() || !composeSubject.trim() || !composeBody.trim()) return
    setSending(true)
    setSendResult(null)
    setError(null)
    try {
      const payload = {
        to: composeTo,
        subject: composeSubject,
        body: composeBody,
      }
      if (composeFiles.length > 0) {
        payload.attachments = composeFiles
      }
      const res = await sendGmailEmail(payload)
      if (res.success) {
        setSendResult(res.message)
        setComposeTo('')
        setComposeSubject('')
        setComposeBody('')
        setComposeFiles([])
      } else {
        setError(res.error || "Erreur lors de l'envoi")
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSending(false)
    }
  }, [composeTo, composeSubject, composeBody, composeFiles])

  // -- Reply shortcut from detail view
  const handleReplyTo = useCallback((email) => {
    setComposeTo(email.from || '')
    setComposeSubject(`Re: ${email.subject || ''}`)
    setComposeBody('')
    setActiveTab('compose')
  }, [])

  // -- File helpers for compose
  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} o`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`
  }

  const handleAddFiles = useCallback((newFiles) => {
    setComposeFiles((prev) => [...prev, ...Array.from(newFiles)])
  }, [])

  const handleRemoveFile = useCallback((index) => {
    setComposeFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length > 0) {
      handleAddFiles(e.dataTransfer.files)
    }
  }, [handleAddFiles])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragOver(false)
  }, [])

  // -- Load categories on connect
  const loadCategories = useCallback(async () => {
    try {
      const res = await fetchGmailCategories()
      setCategories(res.categories || {})
    } catch {
      // silent
    }
  }, [])

  useEffect(() => {
    if (status?.connected) {
      loadCategories()
    }
  }, [status?.connected, loadCategories])

  // -- Set category on email (manual override)
  const handleSetCategory = useCallback(async (uid, category) => {
    try {
      if (category) {
        await categorizeGmailEmail(uid, category)
        setEmails((prev) => prev.map((em) =>
          em.uid === uid ? { ...em, category } : em
        ))
      } else {
        await uncategorizeGmailEmail(uid)
        setEmails((prev) => prev.map((em) =>
          em.uid === uid ? { ...em, category: 'Personnel' } : em
        ))
      }
    } catch (err) {
      setError(err.message)
    }
  }, [])

  // -- Set status on email
  const handleSetStatus = useCallback(async (uid, newStatus) => {
    try {
      await setGmailEmailStatus(uid, newStatus)
      setEmails((prev) => prev.map((em) =>
        em.uid === uid ? { ...em, status: newStatus } : em
      ))
    } catch (err) {
      setError(err.message)
    }
  }, [])

  // -- Date filter change
  const handleDateFilterChange = useCallback((filter) => {
    setDateFilter(filter)
    setCurrentPage(1)
    handleFetchEmails(filter, 1)
  }, [handleFetchEmails])

  // -- Page change
  const handlePageChange = useCallback((page) => {
    setCurrentPage(page)
    handleFetchEmails(dateFilter, page)
  }, [handleFetchEmails, dateFilter])

  // -- Category counts (global from backend)
  const categoryCounts = globalCategoryCounts

  // -- Render -----------------------------------------------------------------

  const isConnected = status?.connected

  return (
    <div className="gmail-page">
      {/* Header */}
      <div className="gm-header">
        <div className="gm-header-icon-wrap">
          <IconMail />
        </div>
        <div className="gm-header-text">
          <h2>Gmail</h2>
          <p className="gm-header-subtitle">
            Lire, resumer et rediger vos mails avec l'aide de l'IA
          </p>
        </div>
        <div className="gm-header-status">
          {status && (
            <span className={`gm-status-pill ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="gm-status-dot" />
              {isConnected ? 'Connecte' : 'Deconnecte'}
            </span>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="gm-error">
          <span>{error}</span>
          <button className="gm-error-close" onClick={() => setError(null)}>&times;</button>
        </div>
      )}

      {/* Connect card (when not connected) */}
      {status && !isConnected && (
        <div className="gm-connect-card">
          <div className="gm-connect-visual">
            <svg width="80" height="64" viewBox="0 0 80 64" fill="none">
              <rect x="4" y="8" width="72" height="48" rx="6" stroke="var(--text-secondary)" strokeWidth="2" fill="none" opacity="0.3" />
              <path d="M4 14l36 24 36-24" stroke="var(--text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.3" />
              <circle cx="40" cy="36" r="12" fill="rgba(234,67,53,0.1)" stroke="#ea4335" strokeWidth="1.5" />
              <path d="M36 36h8M40 32v8" stroke="#ea4335" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <h3>Connecter Gmail</h3>
          <p className="gm-connect-hint">
            {status.message || 'Ajoutez GMAIL_ADDRESS et GMAIL_APP_PASSWORD dans .env'}
          </p>
          <button
            className="gm-btn gm-btn-primary"
            onClick={handleConnect}
            disabled={connecting || !status.available}
          >
            {connecting ? 'Connexion...' : 'Connecter'}
          </button>
        </div>
      )}

      {/* Main content (when connected) */}
      {isConnected && (
        <>
          {/* Tab bar */}
          <div className="gm-tabs">
            <button
              className={`gm-tab ${activeTab === 'inbox' ? 'active' : ''}`}
              onClick={() => { setActiveTab('inbox'); setSelectedEmail(null) }}
            >
              <IconInbox />
              Mails non lus
              {emails.length > 0 && <span className="gm-tab-badge">{emails.length}</span>}
            </button>
            <button
              className={`gm-tab ${activeTab === 'compose' ? 'active' : ''}`}
              onClick={() => setActiveTab('compose')}
            >
              <IconEdit />
              Rediger
            </button>
          </div>

          {/* -- INBOX TAB ------------------------------------------------- */}
          {activeTab === 'inbox' && (
            <div className="gm-inbox">
              {/* Toolbar */}
              <div className="gm-toolbar">
                <button
                  className="gm-btn gm-btn-ghost"
                  onClick={() => handleFetchEmails()}
                  disabled={loadingEmails}
                >
                  <IconRefresh />
                  {loadingEmails ? 'Chargement...' : 'Rafraichir'}
                </button>
                <button
                  className="gm-btn gm-btn-accent"
                  onClick={handleSummarize}
                  disabled={summarizing || emails.length === 0}
                >
                  <IconSpark />
                  {summarizing
                    ? 'Resume en cours...'
                    : selectedUids.size > 0
                      ? `Resumer (${selectedUids.size})`
                      : 'Resumer tout'}
                </button>

                {/* Date filters */}
                <div className="gm-filter-group">
                  {[
                    { key: 'today', label: "Aujourd'hui" },
                    { key: 'week', label: 'Semaine' },
                    { key: 'month', label: 'Mois' },
                  ].map((f) => (
                    <button
                      key={f.key}
                      className={`gm-filter-btn ${dateFilter === f.key ? 'active' : ''}`}
                      onClick={() => handleDateFilterChange(f.key)}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Category filters with counters */}
              {Object.keys(categories).length > 0 && (
                <div className="gm-category-filters">
                  <button
                    className={`gm-category-chip ${!categoryFilter ? 'active' : ''}`}
                    onClick={() => setCategoryFilter(null)}
                  >
                    Tous
                    {totalEmails > 0 && <span className="gm-chip-count">{totalEmails}</span>}
                  </button>
                  {Object.entries(categories).map(([name, info]) => {
                    const color = typeof info === 'string' ? info : info.color
                    const count = categoryCounts[name] || 0
                    return (
                      <button
                        key={name}
                        className={`gm-category-chip ${categoryFilter === name ? 'active' : ''}`}
                        style={{ '--cat-color': color }}
                        onClick={() => setCategoryFilter(categoryFilter === name ? null : name)}
                      >
                        <span className="gm-cat-dot" style={{ background: color }} />
                        {name}
                        {count > 0 && <span className="gm-chip-count">{count}</span>}
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Summary card */}
              {summary && (
                <div className="gm-summary-card">
                  <div className="gm-summary-header">
                    <IconSpark />
                    <span>Resume IA ({summary.count} mail{summary.count > 1 ? 's' : ''})</span>
                    <button className="gm-summary-close" onClick={() => setSummary(null)}>&times;</button>
                  </div>
                  <div className="gm-summary-body">{summary.summary}</div>
                </div>
              )}

              {/* Email detail view */}
              {selectedEmail && !loadingDetail && (
                <div className="gm-detail-card">
                  <div className="gm-detail-header">
                    <button className="gm-btn gm-btn-ghost" onClick={() => setSelectedEmail(null)}>
                      <IconBack />
                      Retour
                    </button>
                    <button className="gm-btn gm-btn-ghost" onClick={() => handleReplyTo(selectedEmail)}>
                      <IconEdit />
                      Repondre
                    </button>
                  </div>
                  <h3 className="gm-detail-subject">{selectedEmail.subject}</h3>
                  <div className="gm-detail-meta">
                    <span>De: {selectedEmail.from}</span>
                    <span>A: {selectedEmail.to}</span>
                    <span>{selectedEmail.date}</span>
                  </div>
                  <div className="gm-detail-body">{selectedEmail.body}</div>
                  {selectedEmail.attachments && selectedEmail.attachments.length > 0 && (
                    <div className="gm-attachments">
                      <div className="gm-attachments-header">
                        <IconAttachment />
                        <span>{selectedEmail.attachments.length} piece(s) jointe(s)</span>
                      </div>
                      {selectedEmail.attachments.map((att) => (
                        <div key={att.part_index} className="gm-attachment-item">
                          <IconFile />
                          <span className="gm-attachment-name">{att.filename}</span>
                          <span className="gm-attachment-size">{formatSize(att.size)}</span>
                          <a
                            className="gm-btn gm-btn-ghost gm-btn-sm"
                            href={`/api/gmail/email/${encodeURIComponent(selectedEmail.uid)}/attachment/${att.part_index}`}
                            download={att.filename}
                            onClick={(e) => e.stopPropagation()}
                          >
                            <IconDownload />
                            Telecharger
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {loadingDetail && (
                <div className="gm-loading">Chargement du mail...</div>
              )}

              {/* Email list */}
              {!selectedEmail && (
                <>
                  {loadingEmails && <div className="gm-loading">Chargement des mails...</div>}
                  {!loadingEmails && filteredEmails.length === 0 && (
                    <div className="gm-empty">
                      <IconInbox />
                      <p>Aucun mail non lu</p>
                    </div>
                  )}
                  {!loadingEmails && filteredEmails.length > 0 && (
                    <div className="gm-email-list">
                      {/* Select all checkbox */}
                      <div className="gm-select-all-row">
                        <label className="gm-checkbox" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={selectedUids.size === filteredEmails.length && filteredEmails.length > 0}
                            onChange={toggleSelectAll}
                          />
                          <span className="gm-checkbox-label">
                            {selectedUids.size > 0 ? `${selectedUids.size} selectionne(s)` : 'Tout selectionner'}
                          </span>
                        </label>
                      </div>
                      {filteredEmails.map((em) => {
                        const catInfo = categories[em.category]
                        const catColor = catInfo ? (typeof catInfo === 'string' ? catInfo : catInfo.color) : '#888'
                        const statusColor = STATUS_COLORS[em.status] || '#888'

                        return (
                          <div
                            key={em.uid}
                            className={`gm-email-row ${selectedUids.has(em.uid) ? 'gm-row-selected' : ''}`}
                            onClick={() => handleReadEmail(em.uid)}
                          >
                            <label className="gm-checkbox" onClick={(e) => e.stopPropagation()}>
                              <input
                                type="checkbox"
                                checked={selectedUids.has(em.uid)}
                                onChange={() => toggleSelectUid(em.uid)}
                              />
                            </label>
                            <div className="gm-email-from">
                              {em.from}
                              {em.category && (
                                <span
                                  className="gm-cat-badge"
                                  style={{ background: catColor }}
                                >
                                  {em.category}
                                </span>
                              )}
                              {em.ai && (
                                <span className="gm-ai-badge" title="Classe par IA">
                                  <IconSpark />
                                </span>
                              )}
                              {em.status && (
                                <span
                                  className="gm-status-badge"
                                  style={{ '--status-color': statusColor }}
                                >
                                  {em.status}
                                </span>
                              )}
                            </div>
                            <div className="gm-email-subject">{em.subject}</div>
                            <div className="gm-email-preview">{em.preview}</div>
                            <div className="gm-email-date-cat">
                              <span className="gm-email-date">
                                {em.has_attachments && <span className="gm-attachment-icon" title={`${em.attachment_count} piece(s) jointe(s)`}><IconAttachment /></span>}
                                {em.date?.split('T')[0]}
                              </span>
                              <select
                                className="gm-cat-select"
                                value={em.category || ''}
                                onClick={(e) => e.stopPropagation()}
                                onChange={(e) => handleSetCategory(em.uid, e.target.value)}
                              >
                                <option value="">--</option>
                                {Object.keys(categories).map((cat) => (
                                  <option key={cat} value={cat}>{cat}</option>
                                ))}
                              </select>
                              <select
                                className="gm-status-select"
                                value={em.status || 'Nouveau'}
                                onClick={(e) => e.stopPropagation()}
                                onChange={(e) => handleSetStatus(em.uid, e.target.value)}
                              >
                                {STATUS_LIST.map((s) => (
                                  <option key={s} value={s}>{s}</option>
                                ))}
                              </select>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Pagination */}
                  {!loadingEmails && totalPages > 1 && (
                    <div className="gm-pagination">
                      <button
                        className="gm-page-btn"
                        disabled={currentPage <= 1}
                        onClick={() => handlePageChange(currentPage - 1)}
                      >
                        &laquo; Prec.
                      </button>
                      {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter((p) => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 2)
                        .reduce((acc, p, idx, arr) => {
                          if (idx > 0 && p - arr[idx - 1] > 1) {
                            acc.push('...')
                          }
                          acc.push(p)
                          return acc
                        }, [])
                        .map((item, idx) =>
                          item === '...' ? (
                            <span key={`dots-${idx}`} className="gm-page-dots">...</span>
                          ) : (
                            <button
                              key={item}
                              className={`gm-page-btn ${currentPage === item ? 'active' : ''}`}
                              onClick={() => handlePageChange(item)}
                            >
                              {item}
                            </button>
                          )
                        )}
                      <button
                        className="gm-page-btn"
                        disabled={currentPage >= totalPages}
                        onClick={() => handlePageChange(currentPage + 1)}
                      >
                        Suiv. &raquo;
                      </button>
                      <span className="gm-page-info">
                        {totalEmails} mail{totalEmails > 1 ? 's' : ''}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* -- COMPOSE TAB ----------------------------------------------- */}
          {activeTab === 'compose' && (
            <div className="gm-compose">
              {sendResult && (
                <div className="gm-send-success">
                  <span>{sendResult}</span>
                  <button onClick={() => setSendResult(null)}>&times;</button>
                </div>
              )}

              <div className="gm-compose-form">
                <div className="gm-field">
                  <label htmlFor="gm-to">A</label>
                  <input
                    id="gm-to"
                    type="email"
                    placeholder="destinataire@example.com"
                    value={composeTo}
                    onChange={(e) => setComposeTo(e.target.value)}
                  />
                </div>
                <div className="gm-field">
                  <label htmlFor="gm-subject">Sujet</label>
                  <input
                    id="gm-subject"
                    type="text"
                    placeholder="Objet du mail"
                    value={composeSubject}
                    onChange={(e) => setComposeSubject(e.target.value)}
                  />
                </div>
                <div className="gm-field">
                  <label htmlFor="gm-body">Message</label>
                  <textarea
                    id="gm-body"
                    rows={10}
                    className={dragOver ? 'gm-dropzone-active' : ''}
                    placeholder="Redigez votre message ici... Ou ecrivez des instructions et cliquez 'Assister' pour que l'IA complete."
                    value={composeBody}
                    onChange={(e) => setComposeBody(e.target.value)}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  />
                </div>

                {/* File attachments */}
                <div className="gm-compose-files-section">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    style={{ display: 'none' }}
                    onChange={(e) => { handleAddFiles(e.target.files); e.target.value = '' }}
                  />
                  <button
                    type="button"
                    className="gm-btn gm-btn-ghost"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <IconAttachment />
                    Joindre des fichiers
                  </button>
                  {composeFiles.length > 0 && (
                    <div className="gm-compose-files">
                      {composeFiles.map((file, idx) => (
                        <div key={idx} className="gm-compose-file-item">
                          <IconFile />
                          <span className="gm-attachment-name">{file.name}</span>
                          <span className="gm-attachment-size">{formatSize(file.size)}</span>
                          <button
                            type="button"
                            className="gm-file-remove"
                            onClick={() => handleRemoveFile(idx)}
                          >
                            <IconClose />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="gm-compose-actions">
                  <button
                    className="gm-btn gm-btn-accent"
                    onClick={handleAssist}
                    disabled={assisting || !composeBody.trim()}
                  >
                    <IconSpark />
                    {assisting ? 'Generation...' : 'Assister (IA)'}
                  </button>
                  <button
                    className="gm-btn gm-btn-primary"
                    onClick={handleSend}
                    disabled={sending || !composeTo.trim() || !composeSubject.trim() || !composeBody.trim()}
                  >
                    <IconSend />
                    {sending ? 'Envoi...' : 'Envoyer'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
