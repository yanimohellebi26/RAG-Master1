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
            <div className="welcome-icon">📚</div>
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
                  {message.role === 'user' ? '👤' : '🤖'}
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
                            📄 Sources utilisées ({message.sources.length})
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
                          <h4 className="chat-video-header">🎥 Vidéos trouvées pour : <em>{message.videos.concept}</em></h4>
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
                                      <span className="chat-video-play">▶</span>
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
                                    🔍 {query}
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
                              ✨ {message.metadata.rewritten_query}
                            </span>
                          )}
                          {message.metadata.steps && (
                            <span className="metadata-item">
                              🔄 {message.metadata.steps.join(' → ')}
                            </span>
                          )}
                          {message.metadata.total_time && (
                            <span className="metadata-item">
                              ⏱️ {message.metadata.total_time.toFixed(1)}s
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
            {isStreaming ? <span className="spinner" /> : '➤'}
          </button>
        </div>
        <p className="input-hint">
          Appuyez sur Entrée pour envoyer, Shift+Entrée pour un retour à la ligne
        </p>
      </form>
    </div>
  )
}
