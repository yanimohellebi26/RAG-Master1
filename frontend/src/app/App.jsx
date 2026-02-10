/**
 * App -- Root component.
 *
 * Wraps the application with context providers and routes.
 * Keep this file thin — all logic lives in contexts and pages.
 */

import React from 'react'
import { AppProvider, useApp } from '../contexts/AppContext'
import { ChatProvider } from '../contexts/ChatContext'
import AppRoutes from '../routes'
import '../styles/app.css'

function AppShell() {
  const { loading } = useApp()

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'var(--background)',
      }}>
        <div className="animate-spin" style={{ fontSize: '2rem' }}>⚙️</div>
      </div>
    )
  }

  return <AppRoutes />
}

export default function App() {
  return (
    <AppProvider>
      <ChatProvider>
        <AppShell />
      </ChatProvider>
    </AppProvider>
  )
}
