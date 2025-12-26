/**
 * ChatInput Component - Input field for user messages
 */

import React, { useState, useRef, useEffect } from 'react'
import { QueryType, RetrievalParams } from '@/types/chat'

interface ChatInputProps {
  onSubmit: (message: string) => void
  isLoading?: boolean
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !isLoading) {
      onSubmit(message)
      setMessage('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e as any)
    }
  }

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [message])

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-300 dark:border-gray-600 p-4">
      {/* Input */}
      <textarea
        ref={textareaRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask your question... (Ctrl+Enter to send)"
        className="w-full p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={isLoading}
        maxLength={4000}
        aria-label="Question input"
      />

      <div className="mt-2 flex justify-between items-center">
        <span className="text-xs text-gray-500">{message.length}/4000</span>
        <button
          type="submit"
          disabled={isLoading || !message.trim()}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
          aria-label="Send message"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </form>
  )
}
