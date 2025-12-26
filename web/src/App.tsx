/**
 * Main App Component
 */

import React, { useState, useEffect } from 'react'
import { ChatMessage } from './components/ChatMessage'
import { ChatInput } from './components/ChatInput'
import { Message, Session } from './types/chat'
import { api } from './services/api'
import { useTheme } from './hooks/useTheme'
import { useLocalStorage } from './hooks/useLocalStorage'
import { v4 as uuidv4 } from 'uuid'

function App() {
  const [theme, setTheme] = useTheme()
  const [messages, setMessages] = useLocalStorage<Message[]>('messages', [])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [queryType, setQueryType] = useState<'general' | 'research' | 'specific' | 'complex'>(
    'general'
  )
  const [k, setK] = useState(5)

  const handleSendMessage = async (content: string, type: string, retrievalK: number) => {
    setError(null)
    setIsLoading(true)

    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      content,
      sender: 'user',
      timestamp: new Date(),
      queryType: type as any,
    }
    setMessages([...messages, userMessage])

    try {
      // Call API
      const response = await api.askQuestion(
        content,
        type as any,
        retrievalK
      )

      // Add assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        content: response.answer,
        sender: 'assistant',
        timestamp: new Date(),
        queryType: type as any,
        metadata: {
          retrievalTimeMs: response.retrieval_time_ms,
          generationTimeMs: response.generation_time_ms,
          documentsUsed: response.documents_used,
          model: response.model,
        },
      }
      setMessages([...messages, userMessage, assistantMessage])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get response'
      setError(errorMessage)
      setMessages([...messages, userMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`h-screen flex flex-col ${theme === 'dark' ? 'dark' : ''}`}>
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">RAG Chatbot</h1>
        <button
          onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
          className="p-2 rounded bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600"
          aria-label="Toggle theme"
        >
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
      </header>

      {/* Messages Container */}
      <main className="flex-1 overflow-y-auto p-4 bg-white dark:bg-gray-900">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
            <p className="text-lg font-medium">Start a conversation</p>
            <p className="text-sm mt-2">Ask a question to begin</p>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} isUser={msg.sender === 'user'} />
            ))}
          </div>
        )}
      </main>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSubmit={handleSendMessage}
        isLoading={isLoading}
        queryType={queryType}
        onQueryTypeChange={(type) => setQueryType(type as any)}
        retrievalParams={{ k, useMMR: false }}
        onRetrievalParamsChange={(params) => setK(params.k)}
      />
    </div>
  )
}

export default App
