/**
 * Generic hook for fetching data from API
 */

import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

interface FetchState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

export function useFetch<T>(
  url: string,
  options?: {
    skip?: boolean
    dependencies?: unknown[]
  }
): FetchState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    error: null,
  })

  const refetch = useCallback(async () => {
    setState({ data: null, loading: true, error: null })
    try {
      const response = await axios.get<T>(url)
      setState({ data: response.data, loading: false, error: null })
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error')
      setState({ data: null, loading: false, error })
    }
  }, [url])

  useEffect(() => {
    if (options?.skip) return

    refetch()
  }, [url, refetch, options?.skip, ...(options?.dependencies || [])])

  return { ...state, refetch }
}
