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
          ←
        </button>
      </div>

      <div className="sidebar-content">
        {/* Subject Filters */}
        <div className="sidebar-section">
          <h3 className="section-title">
            <span>🎯</span>
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
            <span>📚</span>
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
            <span>⚙️</span>
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
            <span>🤖</span>
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
            🗑️ Effacer la conversation
          </button>
        </div>
      </div>

      <div className="sidebar-footer">
        <small>LangChain + ChromaDB + OpenAI</small>
      </div>
    </aside>
  )
}
