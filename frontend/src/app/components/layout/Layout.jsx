/**
 * Layout -- Shared shell (sidebar + header + content area).
 *
 * Every page is rendered inside <Outlet />.
 * Add new navigation items in the `navItems` array below.
 */

import React, { useState } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import Sidebar from '../ui/Sidebar'
import { useApp } from '../../../contexts/AppContext'
import { useChat } from '../../../contexts/ChatContext'

export default function Layout() {
  const { config, theme, toggleTheme } = useApp()
  const { clearMessages } = useChat()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="app">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onClearChat={clearMessages}
      />
      <div className="main-container">
        <header className="topbar">
          <button
            className="btn btn-ghost"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            ☰
          </button>
          <nav className="topbar-nav">
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
              Chat
            </NavLink>
            <NavLink to="/evaluation" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Evaluation
            </NavLink>
            <NavLink to="/youtube" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              YouTube
            </NavLink>
            <NavLink to="/gdrive" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Drive
            </NavLink>
          </nav>
          <h1 className="topbar-title gradient-text">
            RAG — Master 1
          </h1>
          <div className="topbar-actions">
            <button className="btn btn-ghost" onClick={toggleTheme} aria-label="Toggle theme">
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        {/* Page content rendered by React Router */}
        <Outlet />
      </div>
    </div>
  )
}
