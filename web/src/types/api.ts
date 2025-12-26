/**
 * API Types - TypeScript interfaces for backend API responses and requests
 */

export interface Document {
  title: string
  content: string
  metadata?: Record<string, unknown>
}

export interface RAGResponse {
  answer: string
  query_type: 'general' | 'research' | 'specific' | 'complex'
  documents_used: number
  retrieval_time_ms: number
  generation_time_ms: number
  total_time_ms: number
  sources: Array<{
    title: string
    content: string
    relevance_score: number
    metadata?: Record<string, unknown>
  }>
  model: string
}

export interface InitializeResponse {
  status: string
  total_documents: number
  total_chunks: number
  total_vectors: number
  collection_name: string
  processing_time_ms: number
  estimated_cost_usd: number
}

export interface SearchResponse {
  documents: Document[]
  count: number
  search_time_ms: number
}

export interface StatsResponse {
  status: string
  collection_stats: {
    name: string
    document_count: number
    vector_count: number
    collection_size_mb: number
  }
  pipeline_health: {
    status: 'healthy' | 'degraded' | 'unhealthy'
    qdrant_connected: boolean
    redis_connected: boolean
  }
  timestamp: string
}

export interface DeleteResponse {
  status: string
  message: string
}

export interface HealthResponse {
  status: 'ok' | 'error'
  version: string
  environment: string
  timestamp: string
}
