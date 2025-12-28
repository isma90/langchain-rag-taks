/**
 * Conversation Sidebar Component
 * Displays list of previous conversations and allows switching between them
 */

import React from 'react'
import { Session } from '../types/chat'

interface ConversationSidebarProps {
  sessions: Session[]
  currentSessionId: string
  onSelectSession: (sessionId: string) => void
  onNewConversation: () => void
  isOpen: boolean
  onToggle: () => void
}

export function ConversationSidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewConversation,
  isOpen,
  onToggle,
}: ConversationSidebarProps) {
  const formatDate = (date: Date) => {
    const d = new Date(date)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (d.toDateString() === today.toDateString()) {
      return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else if (d.toDateString() === yesterday.toDateString()) {
      return 'Yesterday'
    } else {
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
  }

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed md:relative
          left-0 top-0 h-screen
          w-64 bg-gray-50 dark:bg-gray-800
          border-r border-gray-200 dark:border-gray-700
          flex flex-col
          transition-transform duration-300 ease-in-out
          z-50 md:z-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Close button for mobile */}
        <button
          onClick={onToggle}
          className="md:hidden absolute top-4 right-4 p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
          aria-label="Close sidebar"
        >
          ✕
        </button>

        {/* New Conversation Button */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={onNewConversation}
            className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded font-medium transition"
          >
            ➕ New Chat
          </button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto p-3">
          {sessions.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 p-4">
              No conversations yet
            </p>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => {
                    onSelectSession(session.id)
                    onToggle() // Close sidebar on mobile after selecting
                  }}
                  className={`
                    w-full text-left px-3 py-2 rounded transition
                    ${
                      currentSessionId === session.id
                        ? 'bg-blue-500 text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                    }
                  `}
                  title={session.title}
                >
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{session.title}</p>
                      <p className="text-xs opacity-75 mt-1">
                        {session.messages.length} messages
                      </p>
                    </div>
                  </div>
                  <p className="text-xs opacity-60 mt-1">{formatDate(session.updatedAt)}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
          <p>{sessions.length} conversation{sessions.length !== 1 ? 's' : ''}</p>
        </div>
      </aside>

      {/* Mobile Toggle Button */}
      <button
        onClick={onToggle}
        className={`
          md:hidden fixed bottom-20 right-4 z-40
          w-12 h-12 rounded-full
          bg-blue-500 hover:bg-blue-600 text-white
          flex items-center justify-center
          shadow-lg transition
          ${isOpen ? 'hidden' : ''}
        `}
        aria-label="Toggle sidebar"
      >
        ☰
      </button>
    </>
  )
}
