import React from 'react'
import { useApp } from '../../../contexts/AppContext'
import './Sidebar.css'

export default function Sidebar({ open, onClose, onClearChat }) {
  const { config, settings, updateSettings } = useApp()

  if (!config) return null

  const handleSubjectToggle = (subject) => {
    const newSubjects = settings.subjects.includes(subject)
      ? settings.subjects.filter(s => s !== subject)
      : [...settings.subjects, subject]
    updateSettings({ subjects: newSubjects })
  }

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-icon">M1</div>
          <div className="logo-text">RAG Assistant</div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Close sidebar">
          {/* Arrow-left icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <div className="sidebar-content">
        {/* Subject Filters */}
        <div className="sidebar-section">
          <h3 className="section-title">
            {/* Funnel / filter icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
            </svg>
            Filtrer par matière
          </h3>
          <div className="subject-chips">
            {config.subjects.map(subject => (
              <label key={subject} className="chip">
                <input
                  type="checkbox"
                  checked={settings.subjects.includes(subject)}
                  onChange={() => handleSubjectToggle(subject)}
                />
                <span className="chip-label">{subject}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Sources slider */}
        <div className="sidebar-section">
          <h3 className="section-title">
            {/* Book / stack icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            Nombre de sources
            <span className="badge badge-info">{settings.nbSources}</span>
          </h3>
          <input
            type="range"
            min="2"
            max="30"
            value={settings.nbSources}
            onChange={(e) => updateSettings({ nbSources: parseInt(e.target.value) })}
            className="range-input"
          />
        </div>

        {/* Pipeline settings */}
        <div className="sidebar-section">
          <h3 className="section-title">
            {/* Gear / settings icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            Pipeline RAG
          </h3>
          <div className="toggle-group">
            <label className="toggle-row">
              <span className="toggle-label">Reformulation de requête</span>
              <input
                type="checkbox"
                checked={settings.enableRewrite}
                onChange={(e) => updateSettings({ enableRewrite: e.target.checked })}
              />
            </label>
            <label className="toggle-row">
              <span className="toggle-label">Recherche hybride (BM25 + sémantique)</span>
              <input
                type="checkbox"
                checked={settings.enableHybrid}
                onChange={(e) => updateSettings({ enableHybrid: e.target.checked })}
              />
            </label>
            <label className="toggle-row">
              <span className="toggle-label">Re-ranking LLM</span>
              <input
                type="checkbox"
                checked={settings.enableRerank}
                onChange={(e) => updateSettings({ enableRerank: e.target.checked })}
              />
            </label>
            <label className="toggle-row">
              <span className="toggle-label">Compression contextuelle</span>
              <input
                type="checkbox"
                checked={settings.enableCompress}
                onChange={(e) => updateSettings({ enableCompress: e.target.checked })}
              />
            </label>
          </div>
        </div>

        {/* Copilot */}
        <div className="sidebar-section">
          <h3 className="section-title">
            {/* Bot / sparkle icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <circle cx="12" cy="5" r="2" />
              <path d="M12 7v4" />
              <line x1="8" y1="16" x2="8" y2="16" />
              <line x1="16" y1="16" x2="16" y2="16" />
            </svg>
            Copilot Tools
          </h3>
          {config.copilot_available ? (
            <>
              {config.copilot_ready ? (
                <div className="badge badge-success">Connecté</div>
              ) : (
                <div className="badge badge-warning">SDK installé — non connecté</div>
              )}
              <select
                value={settings.copilotModel}
                onChange={(e) => updateSettings({ copilotModel: e.target.value })}
                className="select-input"
              >
                {config.copilot_models.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </>
          ) : (
            <>
              <div className="badge badge-info">SDK non installé</div>
              <code className="text-xs">pip install github-copilot-sdk</code>
            </>
          )}
        </div>

        {/* Actions */}
        <div className="sidebar-section">
          <button className="btn btn-danger btn-full" onClick={onClearChat}>
            {/* Trash icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              style={{ flexShrink: 0 }}
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <path d="M10 11v6" />
              <path d="M14 11v6" />
              <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
            </svg>
            Effacer la conversation
          </button>
        </div>
      </div>

      <div className="sidebar-footer">
        <small>LangChain + ChromaDB + OpenAI</small>
      </div>
    </aside>
  )
}
