/**
 * IndexVideoButton — Discreet inline button to index a YouTube video
 * into ChromaDB. Shows a small subject selector on click, then indexes.
 */
import React, { useState, useRef, useEffect } from 'react'
import { useApp } from '../../../contexts/AppContext'
import { indexYouTubeTranscript } from '../../../services/api'
import './IndexVideoButton.css'

export default function IndexVideoButton({ videoUrl, videoId }) {
  const { config } = useApp()
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState('idle')   // idle | picking | loading | done | error
  const [subject, setSubject] = useState('')
  const ref = useRef(null)

  const subjects = config?.subjects || []

  // Close picker on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
        if (status === 'picking') setStatus('idle')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open, status])

  const handleClick = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (status === 'done') return
    setOpen(true)
    setStatus('picking')
  }

  const handleIndex = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (!subject) return
    setStatus('loading')
    try {
      const url = videoUrl || (videoId ? `https://www.youtube.com/watch?v=${videoId}` : '')
      await indexYouTubeTranscript({
        video_url: url,
        subject,
        doc_type: 'Video',
      })
      setStatus('done')
      setOpen(false)
      // Reset after a few seconds
      setTimeout(() => setStatus('idle'), 4000)
    } catch (err) {
      console.error('Index failed:', err)
      setStatus('error')
      setTimeout(() => { setStatus('idle'); setOpen(false) }, 3000)
    }
  }

  const label = {
    idle: '📥',
    picking: '📥',
    loading: '⏳',
    done: '✅',
    error: '❌',
  }[status]

  const title = {
    idle: 'Indexer dans ChromaDB',
    picking: 'Choisir la matière',
    loading: 'Indexation en cours…',
    done: 'Indexée !',
    error: 'Erreur d\'indexation',
  }[status]

  return (
    <span className="index-video-btn-wrapper" ref={ref}>
      <button
        className={`index-video-btn index-video-btn--${status}`}
        onClick={handleClick}
        title={title}
        disabled={status === 'loading'}
      >
        {status === 'loading' ? <span className="spinner-tiny" /> : label}
      </button>

      {open && status === 'picking' && (
        <div className="index-video-picker" onClick={e => e.stopPropagation()}>
          <span className="index-video-picker-label">Matière :</span>
          <select
            id="index-video-subject"
            name="index-video-subject"
            className="index-video-picker-select"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            autoFocus
          >
            <option value="">--</option>
            {subjects.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button
            className="index-video-picker-go"
            onClick={handleIndex}
            disabled={!subject}
          >
            OK
          </button>
        </div>
      )}
    </span>
  )
}
