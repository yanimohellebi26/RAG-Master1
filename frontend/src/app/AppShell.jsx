/**
 * AppShell -- Renders root routes once config is loaded.
 *
 * Separated from App.jsx so React Fast Refresh (Vite HMR)
 * never re-renders this component outside its <AppProvider>.
 */

import React from 'react'
import { useApp } from '../contexts/AppContext'
import AppRoutes from '../routes'

export default function AppShell() {
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
