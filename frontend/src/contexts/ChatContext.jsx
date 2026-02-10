/**
 * ChatContext -- Chat state management (messages, history, streaming).
 *
 * Encapsulates all chat logic so any page can use the chat
 * functionality without duplicating state/logic.
 */

import React, { createContext, useContext, useState, useCallback } from 'react'
import { sendChatMessage, clearChat as apiClearChat } from '../services/api'
import { useApp } from './AppContext'

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const { settings } = useApp()
  const [messages, setMessages] = useState([])
  const [currentContext, setCurrentContext] = useState(null)
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = useCallback(async (question) => {
    const userMessage = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])

    const assistantMessage = {
      role: 'assistant',
      content: '',
      sources: [],
      metadata: {},
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, assistantMessage])
    setIsStreaming(true)

    // We need the index *after* both messages are pushed
    const messageIndex = messages.length + 1

    try {
      const reader = await sendChatMessage({
        question,
        subjects: settings.subjects,
        nb_sources: settings.nbSources,
        enable_rewrite: settings.enableRewrite,
        enable_hybrid: settings.enableHybrid,
        enable_rerank: settings.enableRerank,
        enable_compress: settings.enableCompress,
      })

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))

          if (data.type === 'meta') {
            setMessages(prev => {
              const next = [...prev]
              next[messageIndex] = {
                ...next[messageIndex],
                sources: data.sources,
                metadata: {
                  retrieval_time: data.retrieval_time,
                  rewritten_query: data.rewritten_query,
                  steps: data.steps,
                  num_docs: data.num_docs,
                },
              }
              return next
            })
            setCurrentContext(data.context)
          } else if (data.type === 'token') {
            setMessages(prev => {
              const next = [...prev]
              next[messageIndex] = {
                ...next[messageIndex],
                content: next[messageIndex].content + data.content,
              }
              return next
            })
          } else if (data.type === 'done') {
            setMessages(prev => {
              const next = [...prev]
              next[messageIndex] = {
                ...next[messageIndex],
                metadata: {
                  ...next[messageIndex].metadata,
                  total_time: data.total_time,
                },
              }
              return next
            })
          }
        }
      }
    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => {
        const next = [...prev]
        next[messageIndex] = {
          ...next[messageIndex],
          content: `Erreur: ${err.message || 'Impossible de contacter le serveur.'}`,
          error: true,
        }
        return next
      })
    } finally {
      setIsStreaming(false)
    }
  }, [messages.length, settings])

  const clearMessages = useCallback(async () => {
    try {
      await apiClearChat()
    } catch (err) {
      console.error('Failed to clear chat:', err)
    }
    setMessages([])
    setCurrentContext(null)
  }, [])

  const value = {
    messages,
    currentContext,
    isStreaming,
    sendMessage,
    clearMessages,
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within <ChatProvider>')
  return ctx
}
