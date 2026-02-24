import React, { useState, useRef, useEffect, useMemo } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import { useChat } from '../../../contexts/ChatContext'
import IndexVideoButton from '../ui/IndexVideoButton'
import SaveToNotionButton from '../ui/SaveToNotionButton'
import './ChatArea.css'
import 'highlight.js/styles/github-dark.css'

// Configure marked to use highlight.js
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true,
})

/** Render markdown to sanitized HTML. */
function renderMarkdown(text) {
  const raw = marked(text || '')
  return DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } })
}

// SVG icon components

/** Book/graduation cap illustration — replaces 📚 */
function IconBook({ size = 48, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  )
}

/** User silhouette icon — replaces 👤 */
function IconUser({ size = 20, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
    </svg>
  )
}

/** Sparkle/bot icon — replaces 🤖 */
function IconBot({ size = 20, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" y1="16" x2="8" y2="16" strokeWidth="2.5" />
      <line x1="12" y1="16" x2="12" y2="16" strokeWidth="2.5" />
      <line x1="16" y1="16" x2="16" y2="16" strokeWidth="2.5" />
    </svg>
  )
}

/** Document icon — replaces 📄 */
function IconDocument({ size = 14, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  )
}

/** Play-circle icon — replaces 🎥 */
function IconPlayCircle({ size = 16, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <polygon points="10 8 16 12 10 16 10 8" fill="currentColor" stroke="none" />
    </svg>
  )
}

/** Search icon — replaces 🔍 */
function IconSearch({ size = 14, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  )
}

/** Sparkle icon — replaces ✨ */
function IconSparkle({ size = 14, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z" />
    </svg>
  )
}

/** Arrows-rotate icon — replaces 🔄 */
function IconArrowsRotate({ size = 14, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M21 2v6h-6" />
      <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
      <path d="M3 22v-6h6" />
      <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
    </svg>
  )
}

/** Clock icon — replaces ⏱️ */
function IconClock({ size = 14, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  )
}

/** Send/arrow-up icon — replaces ➤ */
function IconSend({ size = 18, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" fill="currentColor" stroke="none" />
    </svg>
  )
}

export default function ChatArea({ onOpenCopilot }) {
  const { messages, sendMessage, isStreaming } = useChat()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const handleSubmit = async (e) => {
    e?.preventDefault()
    if (!input.trim() || isStreaming) return

    const question = input.trim()
    setInput('')
    await sendMessage(question)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const suggestions = [
    "Quelle est la complexité du tri fusion ?",
    "Expliquer l'unification en Prolog",
    "Qu'est-ce que le pattern MVC ?",
    "Différence entre apprentissage supervisé et non supervisé",
  ]

  return (
    <div className="chat-area">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="welcome-icon">
              <IconBook size={48} />
            </div>
            <h2 className="welcome-title gradient-text">Assistant RAG — Master 1</h2>
            <p className="welcome-subtitle">
              Posez vos questions sur vos cours : Algo, IA, Logique, Systèmes Distribués...
            </p>
            <div className="welcome-suggestions">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  className="suggestion-chip"
                  onClick={() => {
                    setInput(suggestion)
                    textareaRef.current?.focus()
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, idx) => (
              <div key={idx} className={`message message-${message.role}`}>
                <div className="message-avatar">
                  {message.role === 'user' ? (
                    <IconUser size={20} />
                  ) : (
                    <IconBot size={20} />
                  )}
                </div>
                <div className="message-content">
                  {message.role === 'user' ? (
                    <p>{message.content}</p>
                  ) : (
                    <>
                      <div
                        className="message-text"
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content || 'Génération en cours...') }}
                      />
                      {message.sources && message.sources.length > 0 && (
                        <details className="sources-details">
                          <summary>
                            <IconDocument size={14} />
                            {' '}Sources utilisées ({message.sources.length})
                          </summary>
                          <div className="sources-list">
                            {message.sources.map((source, sidx) => (
                              <div key={sidx} className="source-card">
                                <span className="source-badge">{source.matiere}</span>
                                <span className="source-type">{source.doc_type}</span>
                                <span className="source-filename">{source.filename}</span>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                      {message.videos && message.videos.videos && message.videos.videos.length > 0 && (
                        <div className="chat-video-results">
                          <h4 className="chat-video-header">
                            <IconPlayCircle size={16} />
                            {' '}Vidéos trouvées pour : <em>{message.videos.concept}</em>
                          </h4>
                          <div className="chat-video-grid">
                            {message.videos.videos.map((video, vidx) => (
                              <div key={vidx} className="chat-video-card-wrapper">
                                <a
                                  href={video.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="chat-video-card"
                                >
                                  <div className="chat-video-thumb">
                                    {video.thumbnail ? (
                                      <img src={video.thumbnail} alt={video.title} loading="lazy" />
                                    ) : (
                                      <span className="chat-video-play"><svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><polygon points="10 8 16 12 10 16 10 8"/></svg></span>
                                    )}
                                    {video.duration && <span className="chat-video-duration">{video.duration}</span>}
                                  </div>
                                  <div className="chat-video-info">
                                    <span className="chat-video-title">{video.title}</span>
                                    <span className="chat-video-channel">{video.channel}</span>
                                  </div>
                                </a>
                                <span className="chat-video-index-btn">
                                  <IndexVideoButton videoUrl={video.url} />
                                </span>
                              </div>
                            ))}
                          </div>
                          {message.videos.queries && message.videos.queries.length > 0 && (
                            <div className="chat-video-search-links">
                              {message.videos.queries.map((q, qidx) => {
                                const query = typeof q === 'string' ? q : q.query
                                return (
                                  <a
                                    key={qidx}
                                    href={`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="chat-video-search-btn"
                                  >
                                    <IconSearch size={14} />
                                    {' '}{query}
                                  </a>
                                )
                              })}
                            </div>
                          )}
                        </div>
                      )}
                      {message.metadata && (
                        <div className="message-metadata">
                          {message.metadata.rewritten_query && message.metadata.rewritten_query !== messages[idx-1]?.content && (
                            <span className="metadata-item" title="Requête enrichie">
                              <IconSparkle size={14} />
                              {' '}{message.metadata.rewritten_query}
                            </span>
                          )}
                          {message.metadata.steps && (
                            <span className="metadata-item">
                              <IconArrowsRotate size={14} />
                              {' '}{message.metadata.steps.join(' → ')}
                            </span>
                          )}
                          {message.metadata.total_time && (
                            <span className="metadata-item">
                              <IconClock size={14} />
                              {' '}{message.metadata.total_time.toFixed(1)}s
                            </span>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (
        <div className="copilot-actions">
          <button className="btn btn-secondary btn-sm" onClick={onOpenCopilot}>
            Outils Copilot
          </button>
          <SaveToNotionButton
            messages={messages}
            sources={messages[messages.length - 1]?.sources || []}
            subjects={[]}
          />
        </div>
      )}

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <div className="input-container">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Posez votre question sur vos cours..."
            rows={1}
            disabled={isStreaming}
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!input.trim() || isStreaming}
            aria-label="Send message"
          >
            {isStreaming ? <span className="spinner" /> : <IconSend size={18} />}
          </button>
        </div>
        <p className="input-hint">
          Appuyez sur Entrée pour envoyer, Shift+Entrée pour un retour à la ligne
        </p>
      </form>
    </div>
  )
}
