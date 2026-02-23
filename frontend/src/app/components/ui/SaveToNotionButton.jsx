import React, { useState } from 'react'
import { saveToNotion, fetchNotionStatus, connectNotion } from '../../../services/api'
import NotionIcon from './NotionIcon'
import './SaveToNotionButton.css'

export default function SaveToNotionButton({ messages, sources, subjects }) {
  const [status, setStatus] = useState('idle') // idle | loading | success | error | needs_oauth
  const [notionUrl, setNotionUrl] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [showTitleInput, setShowTitleInput] = useState(false)
  const [title, setTitle] = useState('')

  const handleClick = async () => {
    if (status === 'success') {
      window.open(notionUrl, '_blank')
      return
    }

    if (!showTitleInput) {
      // Check Notion status first
      try {
        const statusRes = await fetchNotionStatus()
        if (!statusRes.available) {
          setStatus('error')
          setErrorMsg('Notion non disponible (pip install notion-client)')
          return
        }
        if (!statusRes.connected && !statusRes.has_token) {
          // Needs OAuth — redirect to authorize
          window.location.href = statusRes.oauth_url || '/api/notion/oauth/authorize'
          return
        }
        // If has token but not connected, try to connect
        if (!statusRes.connected && statusRes.has_token) {
          await connectNotion()
        }
      } catch (err) {
        // Continue anyway, save-synthesis will handle auth errors
      }

      // Generate a default title from the first user question
      const firstQuestion = messages.find(m => m.role === 'user')
      const defaultTitle = firstQuestion
        ? `Synthese: ${firstQuestion.content.slice(0, 60)}...`
        : `Synthese RAG - ${new Date().toLocaleDateString('fr-FR')}`
      setTitle(defaultTitle)
      setShowTitleInput(true)
      return
    }

    if (!title.trim()) return

    setStatus('loading')
    setErrorMsg('')

    try {
      const result = await saveToNotion({
        title: title.trim(),
        messages: messages.filter(m => m.content),
        sources: sources || [],
        subjects: subjects || [],
      })

      if (result.error) {
        if (result.needs_oauth) {
          window.location.href = '/api/notion/oauth/authorize'
          return
        }
        setStatus('error')
        setErrorMsg(result.error)
      } else {
        setStatus('success')
        setNotionUrl(result.url || '')
        setShowTitleInput(false)
      }
    } catch (err) {
      setStatus('error')
      setErrorMsg(err.message || 'Erreur de sauvegarde')
    }
  }

  const handleCancel = () => {
    setShowTitleInput(false)
    setTitle('')
    setStatus('idle')
  }

  if (showTitleInput && status !== 'success') {
    return (
      <div className="notion-save-form">
        <input
          type="text"
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Titre de la synthese..."
          className="notion-title-input"
          onKeyDown={e => e.key === 'Enter' && handleClick()}
          autoFocus
        />
        <div className="notion-save-actions">
          <button
            className="btn btn-primary btn-sm"
            onClick={handleClick}
            disabled={status === 'loading' || !title.trim()}
          >
            {status === 'loading' ? <span className="spinner" /> : 'Enregistrer'}
          </button>
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleCancel}
            disabled={status === 'loading'}
          >
            Annuler
          </button>
        </div>
        {status === 'error' && <p className="notion-error">{errorMsg}</p>}
      </div>
    )
  }

  return (
    <button
      className={`btn btn-sm ${status === 'success' ? 'btn-success' : 'btn-secondary'}`}
      onClick={handleClick}
      disabled={status === 'loading'}
      title={
        status === 'success'
          ? 'Ouvrir dans Notion'
          : 'Sauvegarder cette conversation dans Notion'
      }
    >
      {status === 'loading' && <span className="spinner" />}
      {status === 'success' && <><NotionIcon size={14} /> Ouvrir dans Notion</>}
      {status === 'error' && <><NotionIcon size={14} /> Erreur - Reessayer</>}
      {status === 'idle' && <><NotionIcon size={14} /> Notion</>}
    </button>
  )
}
