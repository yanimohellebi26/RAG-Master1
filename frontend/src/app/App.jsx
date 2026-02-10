/**
 * App -- Root component.
 *
 * Wraps the application with context providers and routes.
 * Keep this file thin — all logic lives in contexts and pages.
 */

import React from 'react'
import { AppProvider } from '../contexts/AppContext'
import { ChatProvider } from '../contexts/ChatContext'
import AppShell from './AppShell'
import '../styles/app.css'

export default function App() {
  return (
    <AppProvider>
      <ChatProvider>
        <AppShell />
      </ChatProvider>
    </AppProvider>
  )
}
