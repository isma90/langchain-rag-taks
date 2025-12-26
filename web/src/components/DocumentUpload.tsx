/**
 * DocumentUpload Component - Upload documents to RAG system
 */

import React, { useState } from 'react'
import { api } from '../services/api'

interface DocumentInput {
  content: string
  source: string
  metadata?: Record<string, any>
}

export const DocumentUpload: React.FC = () => {
  const [files, setFiles] = useState<File[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const newFiles = Array.from(e.dataTransfer.files)
      setFiles((prev) => [...prev, ...newFiles])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      setFiles((prev) => [...prev, ...newFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select at least one file')
      return
    }

    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      // Read files and prepare documents
      const documents: DocumentInput[] = []

      for (const file of files) {
        const content = await file.text()
        documents.push({
          content,
          source: file.name,
          metadata: {
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            uploadedAt: new Date().toISOString(),
          },
        })
      }

      // Call initialize API
      const response = await api.initializeCollection({
        collection_name: 'rag_documents',
        documents,
        force_recreate: false,
      })

      setSuccess(
        `Successfully uploaded ${documents.length} document(s)! ${response.total_documents} documents total in collection.`
      )
      setFiles([])

      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload documents'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Upload Documents</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Upload your documents to build the RAG knowledge base. Supported formats: text, markdown, PDF
          content
        </p>
      </div>

      {/* Drag and Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          dragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
        }`}
      >
        <input
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="file-input"
          accept=".txt,.md,.pdf"
          aria-label="Select files to upload"
        />
        <label htmlFor="file-input" className="block cursor-pointer">
          <p className="text-4xl mb-2">📄</p>
          <p className="text-lg font-medium mb-1">Drag files here or click to select</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Supported: .txt, .md, and PDF content
          </p>
        </label>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-3">Selected Files ({files.length})</h3>
          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-100 dark:bg-gray-800 rounded"
              >
                <div className="flex items-center gap-2">
                  <span>📄</span>
                  <div>
                    <p className="font-medium text-sm">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="px-3 py-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded transition"
                  aria-label={`Remove ${file.name}`}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 rounded">
          <p className="font-medium">Error</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mt-4 p-4 bg-green-100 dark:bg-green-900 border border-green-400 dark:border-green-700 text-green-700 dark:text-green-200 rounded">
          <p className="font-medium">✓ Success</p>
          <p className="text-sm mt-1">{success}</p>
        </div>
      )}

      {/* Upload Button */}
      <div className="mt-6 flex gap-3">
        <button
          onClick={handleUpload}
          disabled={files.length === 0 || isLoading}
          className="flex-1 px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
          aria-label="Upload documents"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <span className="animate-spin mr-2">⏳</span> Uploading...
            </span>
          ) : (
            'Upload Documents'
          )}
        </button>
        {files.length > 0 && (
          <button
            onClick={() => setFiles([])}
            type="button"
            disabled={isLoading}
            className="px-6 py-3 bg-gray-300 hover:bg-gray-400 dark:bg-gray-700 dark:hover:bg-gray-600 disabled:opacity-50 text-gray-900 dark:text-white rounded-lg font-medium transition"
            aria-label="Clear selected files"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-800 rounded">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          📊 Total files selected: <span className="font-medium">{files.length}</span>
        </p>
        {files.length > 0 && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            📦 Total size: <span className="font-medium">{
              (files.reduce((sum, f) => sum + f.size, 0) / 1024).toFixed(2)
            } KB</span>
          </p>
        )}
      </div>
    </div>
  )
}
