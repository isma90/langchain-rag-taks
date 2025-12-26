/**
 * ChatMessage Component - Display individual chat messages
 */

import React from 'react'
import { Message } from '@/types/chat'
import classNames from 'classnames'

interface ChatMessageProps {
  message: Message
  isUser: boolean
  onCopy?: () => void
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isUser, onCopy }) => {
  const containerClass = classNames('flex mb-4', {
    'justify-end': isUser,
    'justify-start': !isUser,
  })

  const messageClass = classNames('max-w-xs lg:max-w-md px-4 py-2 rounded-lg', {
    'bg-blue-500 text-white': isUser,
    'bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-gray-100': !isUser,
  })

  return (
    <div className={containerClass}>
      <div className={messageClass}>
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        {!isUser && message.metadata && (
          <div className="text-xs mt-2 opacity-75">
            {message.metadata.generationTimeMs && (
              <div>
                Generated in {(message.metadata.generationTimeMs / 1000).toFixed(2)}s
              </div>
            )}
            {message.metadata.documentsUsed && (
              <div>{message.metadata.documentsUsed} documents used</div>
            )}
          </div>
        )}
        <div className="text-xs mt-2 opacity-50">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
