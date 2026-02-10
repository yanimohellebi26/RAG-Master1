/**
 * AppContext -- Global application state (config, theme, settings).
 *
 * Wraps the entire app so every page/component can read config
 * and settings without prop-drilling.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { fetchConfig } from '../services/api'

const AppContext = createContext(null)

const DEFAULT_SETTINGS = {
  subjects: [],
  nbSources: 10,
  enableRewrite: true,
  enableHybrid: true,
  enableRerank: false,
  enableCompress: false,
  copilotModel: 'gpt-4o',
}

export function AppProvider({ children }) {
  const [config, setConfig] = useState(null)
  const [theme, setTheme] = useState('dark')
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [loading, setLoading] = useState(true)

  // Load config on mount
  useEffect(() => {
    fetchConfig()
      .then(data => {
        setConfig(data)
        setSettings(prev => ({
          ...prev,
          copilotModel: data.copilot_models?.[0] || 'gpt-4o',
        }))
      })
      .catch(err => console.error('Failed to load config:', err))
      .finally(() => setLoading(false))
  }, [])

  // Apply theme to DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
  }, [])

  const updateSettings = useCallback((patch) => {
    setSettings(prev => ({ ...prev, ...patch }))
  }, [])

  const value = {
    config,
    loading,
    theme,
    toggleTheme,
    settings,
    updateSettings,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within <AppProvider>')
  return ctx
}
