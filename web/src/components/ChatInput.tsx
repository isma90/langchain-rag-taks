/**
 * ChatInput Component - Input field for user messages
 */

import React, { useState, useRef, useEffect } from 'react'
import { QueryType, RetrievalParams } from '@/types/chat'

interface ChatInputProps {
  onSubmit: (message: string, queryType: string, k: number) => void
  isLoading?: boolean
  queryType?: string
  onQueryTypeChange?: (type: string) => void
  retrievalParams?: RetrievalParams
  onRetrievalParamsChange?: (params: RetrievalParams) => void
}

const QUERY_TYPES: QueryType[] = [
  {
    id: 'general',
    label: 'General',
    description: 'Simple facts, straightforward answers',
    icon: '🔍',
  },
  {
    id: 'research',
    label: 'Research',
    description: 'Comparative analysis, multiple sources',
    icon: '📚',
  },
  {
    id: 'specific',
    label: 'Specific',
    description: 'Domain-specific technical questions',
    icon: '⚙️',
  },
  {
    id: 'complex',
    label: 'Complex',
    description: 'Multi-step reasoning, synthesis',
    icon: '💡',
  },
]

export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  isLoading = false,
  queryType = 'general',
  onQueryTypeChange,
  retrievalParams = { k: 5, useMMR: false },
  onRetrievalParamsChange,
}) => {
  const [message, setMessage] = useState('')
  const [k, setK] = useState(retrievalParams.k)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !isLoading) {
      onSubmit(message, queryType, k)
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
      {/* Query Type Selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Query Type</label>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
          {QUERY_TYPES.map((type) => (
            <button
              key={type.id}
              type="button"
              onClick={() => onQueryTypeChange?.(type.id)}
              className={`p-2 rounded border-2 text-sm font-medium transition ${
                queryType === type.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900 text-blue-900 dark:text-blue-50'
                  : 'border-gray-300 dark:border-gray-600 hover:border-blue-300'
              }`}
              aria-pressed={queryType === type.id}
            >
              <span>{type.icon}</span> {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Retrieval Parameters */}
      <div className="mb-4 space-y-2">
        <div>
          <label htmlFor="k-slider" className="text-sm font-medium">
            Documents to Retrieve (k): {k}
          </label>
          <input
            id="k-slider"
            type="range"
            min="1"
            max="20"
            value={k}
            onChange={(e) => {
              const newK = parseInt(e.target.value)
              setK(newK)
              onRetrievalParamsChange?.({ ...retrievalParams, k: newK })
            }}
            className="w-full"
            aria-label="Number of documents to retrieve"
          />
        </div>
        <label className="flex items-center text-sm">
          <input
            type="checkbox"
            checked={retrievalParams.useMMR}
            onChange={(e) =>
              onRetrievalParamsChange?.({ ...retrievalParams, useMMR: e.target.checked })
            }
            className="mr-2"
            aria-label="Use Maximum Marginal Relevance for diverse results"
          />
          Use MMR (diverse results)
        </label>
      </div>

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
