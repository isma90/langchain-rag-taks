/**
 * Chat Domain Types
 */

export interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  queryType?: 'general' | 'research' | 'specific' | 'complex'
  metadata?: {
    retrievalTimeMs?: number
    generationTimeMs?: number
    documentsUsed?: number
    model?: string
  }
}

export interface Session {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
  metadata?: Record<string, unknown>
}

export interface Collection {
  name: string
  documentCount: number
  vectorCount: number
  sizeMb: number
  createdAt: Date
  lastModified: Date
}

export interface ChunkingStrategy {
  name: 'recursive' | 'semantic' | 'markdown' | 'html'
  label: string
  description: string
}

export interface QueryType {
  id: 'general' | 'research' | 'specific' | 'complex'
  label: string
  description: string
  icon: string
}

export interface RetrievalParams {
  k: number
  useMMR: boolean
  metadataFilter?: string
}
