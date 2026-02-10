/**
 * Routes -- Central route definitions.
 *
 * To add a new page:
 *   1. Create a component in src/pages/
 *   2. Import it here
 *   3. Add a <Route> below
 *   4. Add a <NavLink> in Layout.jsx
 */

import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './app/components/layout/Layout'
import ChatPage from './pages/ChatPage'
import EvaluationPage from './pages/EvaluationPage'
import YouTubePage from './pages/YouTubePage'

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ChatPage />} />
        <Route path="evaluation" element={<EvaluationPage />} />
        <Route path="youtube" element={<YouTubePage />} />
        {/* Add more routes here as you extend the project */}
      </Route>
    </Routes>
  )
}
