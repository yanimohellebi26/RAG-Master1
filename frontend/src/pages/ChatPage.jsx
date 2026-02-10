/**
 * ChatPage -- Main chat interface.
 *
 * This is the "/" route. All chat state comes from ChatContext.
 */

import React, { useState } from 'react'
import ChatArea from '../app/components/chat/ChatArea'
import CopilotPanel from '../app/components/copilot/CopilotPanel'
import { useApp } from '../contexts/AppContext'
import { useChat } from '../contexts/ChatContext'

export default function ChatPage() {
  const { config, settings } = useApp()
  const { messages, currentContext } = useChat()
  const [copilotOpen, setCopilotOpen] = useState(false)

  return (
    <>
      <ChatArea onOpenCopilot={() => setCopilotOpen(true)} />

      {copilotOpen && config && (
        <CopilotPanel
          config={config}
          messages={messages}
          context={currentContext}
          model={settings.copilotModel}
          onClose={() => setCopilotOpen(false)}
        />
      )}
    </>
  )
}
