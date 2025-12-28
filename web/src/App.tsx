/**
 * Main App Component
 */

import React, { useState, useRef, useEffect } from 'react'
import { ChatMessage } from './components/ChatMessage'
import { ChatInput } from './components/ChatInput'
import { DocumentUpload } from './components/DocumentUpload'
import { Message } from './types/chat'
import { api } from './services/api'
import { useTheme } from './hooks/useTheme'
import { useLocalStorage } from './hooks/useLocalStorage'
import { v4 as uuidv4 } from 'uuid'

type View = 'chat' | 'upload'

function App() {
  const [theme, setTheme] = useTheme()
  const [messages, setMessages] = useLocalStorage<Message[]>('messages', [])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentView, setCurrentView] = useState<View>('chat')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (content: string) => {
    setError(null)
    setIsLoading(true)

    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      content,
      sender: 'user',
      timestamp: new Date(),
      queryType: 'general',
    }
    setMessages([...messages, userMessage])

    try {
      // Call API with default parameters
      const response = await api.askQuestion(content, 'general', 5)

      // Add assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        content: response.answer,
        sender: 'assistant',
        timestamp: new Date(),
        queryType: 'general',
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
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">RAG Chatbot</h1>
          <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            className="p-2 rounded bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600"
            aria-label="Toggle theme"
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex gap-2 border-t border-gray-200 dark:border-gray-700 pt-3">
          <button
            onClick={() => setCurrentView('chat')}
            className={`px-4 py-2 rounded-t font-medium transition ${
              currentView === 'chat'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
            aria-selected={currentView === 'chat'}
            role="tab"
          >
            💬 Chat
          </button>
          <button
            onClick={() => setCurrentView('upload')}
            className={`px-4 py-2 rounded-t font-medium transition ${
              currentView === 'upload'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
            aria-selected={currentView === 'upload'}
            role="tab"
          >
            📄 Upload Docs
          </button>
        </nav>
      </header>

      {/* Content Area */}
      {currentView === 'chat' ? (
        <>
          {/* Messages Container */}
          <main className="flex-1 overflow-y-auto p-4 bg-white dark:bg-gray-900">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
                <p className="text-lg font-medium">💬 Start a conversation</p>
                <p className="text-sm mt-2">Ask a question to begin</p>
                <p className="text-xs mt-3 text-gray-400">
                  Make sure you've uploaded documents first!
                </p>
              </div>
            ) : (
              <div className="max-w-4xl mx-auto">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} isUser={msg.sender === 'user'} />
                ))}
                {/* Scroll anchor - always at the bottom */}
                <div ref={messagesEndRef} />
              </div>
            )}
          </main>

          {/* Error Display */}
          {error && (
            <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3">
              <p className="font-medium">Error</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          {/* Input */}
          <ChatInput onSubmit={handleSendMessage} isLoading={isLoading} />
        </>
      ) : (
        /* Upload View */
        <main className="flex-1 overflow-y-auto p-4 bg-white dark:bg-gray-900">
          <DocumentUpload />
        </main>
      )}
    </div>
  )
}

export default App
