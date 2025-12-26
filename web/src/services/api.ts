/**
 * Typed API Client for RAG Backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import {
  RAGResponse,
  InitializeResponse,
  SearchResponse,
  StatsResponse,
  DeleteResponse,
  HealthResponse,
} from '@/types/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Retry logic with exponential backoff
let retryCount = 0
const MAX_RETRIES = 3

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config

    if (!config) throw error

    retryCount = (config as any).retryCount || 0

    const isRetryableError =
      !error.response ||
      error.response.status === 408 ||
      error.response.status === 429 ||
      (error.response.status >= 500 && error.response.status < 600)

    if (retryCount < MAX_RETRIES && isRetryableError) {
      retryCount++
      (config as any).retryCount = retryCount

      const delay = Math.pow(2, retryCount - 1) * 1000
      await new Promise((resolve) => setTimeout(resolve, delay))

      return apiClient(config)
    }

    throw error
  }
)

// API Methods
export const api = {
  /**
   * Check API health
   */
  async getHealth(): Promise<HealthResponse> {
    const { data } = await apiClient.get<HealthResponse>('/health')
    return data
  },

  /**
   * Initialize collection with documents
   */
  async initializeCollection(
    collectionName: string,
    documents: Array<{ title: string; content: string }>,
    chunkingStrategy: string = 'recursive',
    enableMetadata: boolean = true
  ): Promise<InitializeResponse> {
    const { data } = await apiClient.post<InitializeResponse>('/initialize', {
      collection_name: collectionName,
      documents,
      chunking_strategy: chunkingStrategy,
      enable_metadata: enableMetadata,
    })
    return data
  },

  /**
   * Ask question to RAG pipeline
   */
  async askQuestion(
    question: string,
    queryType: 'general' | 'research' | 'specific' | 'complex' = 'general',
    k: number = 5,
    collectionName?: string
  ): Promise<RAGResponse> {
    const { data } = await apiClient.post<RAGResponse>('/question', {
      question,
      query_type: queryType,
      k,
      ...(collectionName && { collection_name: collectionName }),
    })
    return data
  },

  /**
   * Search documents without generating answer
   */
  async searchDocuments(
    query: string,
    k: number = 5,
    queryType: 'general' | 'research' | 'specific' | 'complex' = 'general'
  ): Promise<SearchResponse> {
    const { data } = await apiClient.post<SearchResponse>('/search', {
      query,
      k,
      query_type: queryType,
    })
    return data
  },

  /**
   * Get pipeline and collection statistics
   */
  async getStats(): Promise<StatsResponse> {
    const { data } = await apiClient.get<StatsResponse>('/stats')
    return data
  },

  /**
   * Delete a collection
   */
  async deleteCollection(collectionName: string): Promise<DeleteResponse> {
    const { data } = await apiClient.delete<DeleteResponse>(
      `/collection/${collectionName}`
    )
    return data
  },

  /**
   * Process multiple questions in batch
   */
  async batchAskQuestions(
    questions: string[],
    queryType: 'general' | 'research' | 'specific' | 'complex' = 'general',
    k: number = 5
  ): Promise<Array<RAGResponse>> {
    const { data } = await apiClient.post<Array<RAGResponse>>(
      '/batch-questions',
      {
        questions,
        query_type: queryType,
        k,
      }
    )
    return data
  },
}

export default apiClient
