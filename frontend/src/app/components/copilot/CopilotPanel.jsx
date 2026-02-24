import React, { useState } from 'react'
import { generateCopilotTool, searchYouTubeVideos } from '../../../services/api'
import IndexVideoButton from '../ui/IndexVideoButton'
import SaveToNotionButton from '../ui/SaveToNotionButton'
import './CopilotPanel.css'

export default function CopilotPanel({ config, messages, context, model, onClose }) {
  const [activeTools, setActiveTools] = useState({})
  const [results, setResults] = useState({})
  const [loading, setLoading] = useState({})

  const lastMessage = messages.filter(m => m.role === 'assistant').slice(-1)[0]
  const lastQuestion = messages.filter(m => m.role === 'user').slice(-1)[0]

  const generateTool = async (toolType) => {
    if (!lastMessage || !lastQuestion) return

    setLoading(prev => ({ ...prev, [toolType]: true }))

    // Special handling for notion tool — just show the save UI
    if (toolType === 'notion') {
      setResults(prev => ({ ...prev, [toolType]: { ready: true } }))
      setActiveTools(prev => ({ ...prev, [toolType]: true }))
      setLoading(prev => ({ ...prev, [toolType]: false }))
      return
    }

    // Special handling for video search tool
    if (toolType === 'video') {
      try {
        const result = await searchYouTubeVideos({
          concept: lastQuestion.content,
          context: context?.slice(0, 3000) || '',
          max_results: 5,
        })
        setResults(prev => ({ ...prev, [toolType]: result }))
        setActiveTools(prev => ({ ...prev, [toolType]: true }))
      } catch (err) {
        console.error('Video search failed:', err)
        setResults(prev => ({ ...prev, [toolType]: { error: err.message || 'Erreur de recherche' } }))
        setActiveTools(prev => ({ ...prev, [toolType]: true }))
      } finally {
        setLoading(prev => ({ ...prev, [toolType]: false }))
      }
      return
    }
    
    const content = `Question de l'étudiant : ${lastQuestion.content}\n\nRéponse du cours :\n${lastMessage.content}\n\nExtraits des cours :\n${context?.slice(0, 3000) || ''}`
    
    try {
      const result = await generateCopilotTool({
        toolType,
        content,
        model,
        sources: lastMessage.sources || [],
      })
      setResults(prev => ({ ...prev, [toolType]: result }))
      setActiveTools(prev => ({ ...prev, [toolType]: true }))
    } catch (err) {
      console.error('Copilot generation failed:', err)
      setResults(prev => ({ ...prev, [toolType]: { error: err.message || 'Erreur de generation' } }))
    } finally {
      setLoading(prev => ({ ...prev, [toolType]: false }))
    }
  }

  const renderResult = (toolType, result) => {
    if (result.error) {
      return (
        <div className="error-message">
          <p><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{verticalAlign:'middle',marginRight:'0.3rem'}}><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>{result.error}</p>
          {result.raw && (
            <details>
              <summary>Réponse brute</summary>
              <pre>{result.raw.slice(0, 500)}</pre>
            </details>
          )}
        </div>
      )
    }

    switch (toolType) {
      case 'quiz':
        return <QuizRenderer data={result} />
      case 'table':
        return <TableRenderer data={result} />
      case 'chart':
        return <ChartRenderer data={result} />
      case 'concepts':
        return <ConceptsRenderer data={result} />
      case 'flashcards':
        return <FlashcardsRenderer data={result} />
      case 'mindmap':
        return <MindmapRenderer data={result} />
      case 'video':
        return <VideoRenderer data={result} />
      case 'notion':
        return <NotionRenderer data={result} messages={messages} />
      default:
        return <pre>{JSON.stringify(result, null, 2)}</pre>
    }
  }

  return (
    <div className="copilot-panel-overlay" onClick={onClose}>
      <div className="copilot-panel" onClick={e => e.stopPropagation()}>
        <div className="copilot-header">
          <h2><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{verticalAlign:'middle',marginRight:'0.4rem'}}><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2z"/></svg>Outils Copilot</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Fermer"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>

        <div className="copilot-body">
          <div className="copilot-tools-grid">
            {Object.entries(config.tool_labels || {}).map(([key, label]) => (
              <button
                key={key}
                className="copilot-tool-btn"
                onClick={() => generateTool(key)}
                disabled={loading[key]}
              >
                {loading[key] ? <span className="spinner" /> : label}
              </button>
            ))}
          </div>

          <div className="copilot-results">
            {Object.entries(results).filter(([_, res]) => activeTools[_]).map(([toolType, result]) => (
              <div key={toolType} className="copilot-result-card">
                <div className="result-header">
                  <h3>{config.tool_labels?.[toolType] || toolType}</h3>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => setActiveTools(prev => ({ ...prev, [toolType]: false }))}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                </div>
                <div className="result-body">
                  {renderResult(toolType, result)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// Tool renderers
function QuizRenderer({ data }) {
  const [answers, setAnswers] = useState({})
  
  return (
    <div className="quiz">
      <h4>{data.title}</h4>
      {data.questions?.map((q, idx) => (
        <div key={idx} className="quiz-question">
          <p><strong>Q{idx + 1}.</strong> {q.question}</p>
          <div className="quiz-options">
            {q.options?.map((option, oidx) => (
              <label key={oidx} className="quiz-option">
                <input
                  type="radio"
                  name={`q${idx}`}
                  onChange={() => setAnswers(prev => ({ ...prev, [idx]: oidx }))}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
          {answers[idx] !== undefined && (
            <div className={`quiz-feedback ${answers[idx] === q.correct ? 'correct' : 'incorrect'}`}>
              {answers[idx] === q.correct ? 'Correct !' : `Bonne reponse : ${q.options[q.correct]}`}
              {q.explanation && <p>{q.explanation}</p>}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function TableRenderer({ data }) {
  return (
    <div className="table-container">
      <h4>{data.title}</h4>
      <table>
        <thead>
          <tr>
            {data.headers?.map((h, idx) => <th key={idx}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.rows?.map((row, idx) => (
            <tr key={idx}>
              {row.map((cell, cidx) => <td key={cidx}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ChartRenderer({ data }) {
  return (
    <div className="chart-container">
      <h4>{data.title}</h4>
      <div className="simple-chart">
        {data.labels?.map((label, idx) => (
          <div key={idx} className="chart-bar">
            <span className="chart-label">{label}</span>
            <div className="chart-bar-bg">
              <div 
                className="chart-bar-fill" 
                style={{ width: `${(data.values[idx] / Math.max(...data.values)) * 100}%` }}
              />
            </div>
            <span className="chart-value">{data.values[idx]}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ConceptsRenderer({ data }) {
  return (
    <div className="concepts">
      <h4>{data.title}</h4>
      {data.concepts?.map((concept, idx) => (
        <div key={idx} className={`concept-card concept-${concept.importance}`}>
          <strong>{concept.name}</strong>
          <p>{concept.definition}</p>
        </div>
      ))}
    </div>
  )
}

function FlashcardsRenderer({ data }) {
  return (
    <div className="flashcards">
      <h4>{data.title}</h4>
      {data.cards?.map((card, idx) => (
        <details key={idx} className="flashcard">
          <summary>{card.front}</summary>
          <div className="flashcard-back">{card.back}</div>
        </details>
      ))}
    </div>
  )
}

function MindmapRenderer({ data }) {
  return (
    <div className="mindmap">
      <h4>{data.title}</h4>
      <div className="mindmap-central">{data.central}</div>
      {data.branches?.map((branch, idx) => (
        <div key={idx} className="mindmap-branch">
          <strong>{branch.name}</strong>
          <ul>
            {branch.children?.map((child, cidx) => (
              <li key={cidx}>{child}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

function NotionRenderer({ data, messages }) {
  const lastAssistant = messages.filter(m => m.role === 'assistant').slice(-1)[0]
  const sources = lastAssistant?.sources || []

  return (
    <div className="notion-renderer">
      <p>Sauvegarder cette conversation comme synthese dans Notion :</p>
      <SaveToNotionButton
        messages={messages}
        sources={sources}
        subjects={[]}
      />
    </div>
  )
}

function VideoRenderer({ data }) {
  return (
    <div className="video-results">
      <div className="video-header-info">
        <h4><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{verticalAlign:'middle',marginRight:'0.3rem'}}><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>Videos pour : <em>{data.concept}</em></h4>
        {data.tips && <p className="video-tips"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{verticalAlign:'middle',marginRight:'0.3rem'}}><line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>{data.tips}</p>}
      </div>

      {data.videos && data.videos.length > 0 ? (
        <div className="video-grid">
          {data.videos.map((video, idx) => (
            <div key={idx} className="video-card-wrapper">
              <a
                href={video.url}
                target="_blank"
                rel="noopener noreferrer"
                className="video-card"
              >
                <div className="video-thumbnail">
                  {video.thumbnail ? (
                    <img src={video.thumbnail} alt={video.title} loading="lazy" />
                  ) : (
                    <div className="video-thumb-placeholder"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="10 8 16 12 10 16 10 8"/></svg></div>
                  )}
                  {video.duration && (
                    <span className="video-duration">{video.duration}</span>
                  )}
                </div>
                <div className="video-info">
                  <h5 className="video-title">{video.title}</h5>
                  <span className="video-channel">{video.channel}</span>
                  {video.views && (
                    <span className="video-views">{video.views}</span>
                  )}
                </div>
              </a>
              <span className="copilot-video-index-btn">
                <IndexVideoButton videoUrl={video.url} />
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="video-no-results">Aucune vidéo trouvée. Essayez les liens de recherche ci-dessous.</p>
      )}

      {data.queries && data.queries.length > 0 && (
        <div className="video-search-links">
          <h5><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{verticalAlign:'middle',marginRight:'0.3rem'}}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>Rechercher sur YouTube :</h5>
          {data.queries.map((q, idx) => {
            const query = typeof q === 'string' ? q : q.query
            const desc = typeof q === 'object' ? q.description : ''
            const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`
            return (
              <a
                key={idx}
                href={searchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="video-search-link"
              >
                <span className="search-query">"{query}"</span>
                {desc && <span className="search-desc">{desc}</span>}
                <span className="search-arrow">↗</span>
              </a>
            )
          })}
        </div>
      )}

      {data.recommended_channels && data.recommended_channels.length > 0 && (
        <div className="video-recommended">
          <h5><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{verticalAlign:'middle',marginRight:'0.3rem'}}><rect x="2" y="7" width="20" height="15" rx="2" ry="2"/><polyline points="17 2 12 7 7 2"/></svg>Chaines recommandees :</h5>
          <div className="channel-tags">
            {data.recommended_channels.map((ch, idx) => (
              <a
                key={idx}
                href={`https://www.youtube.com/results?search_query=${encodeURIComponent(ch)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="channel-tag"
              >
                {ch}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
