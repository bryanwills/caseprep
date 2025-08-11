"use client"

import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Upload, FileVideo, FileAudio, X, Play, Clock, Settings, AlertCircle } from 'lucide-react'
import Link from 'next/link'

interface UploadFile {
  id: string
  file: File
  name: string
  size: number
  type: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  error?: string
}

interface TranscriptionSettings {
  language: string
  quality: 'standard' | 'high' | 'premium'
  enableDiarization: boolean
  enableWordTiming: boolean
  customDictionary: boolean
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [selectedMatter, setSelectedMatter] = useState<string>('')
  const [settings, setSettings] = useState<TranscriptionSettings>({
    language: 'en',
    quality: 'standard',
    enableDiarization: true,
    enableWordTiming: true,
    customDictionary: false
  })

  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files)
    }
  }

  const handleFiles = (fileList: FileList) => {
    const newFiles: UploadFile[] = Array.from(fileList).map((file, index) => ({
      id: Date.now().toString() + index,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      progress: 0,
      status: 'uploading'
    }))

    setFiles(prev => [...prev, ...newFiles])

    // Simulate upload progress
    newFiles.forEach(file => {
      simulateUpload(file.id)
    })
  }

  const simulateUpload = (fileId: string) => {
    const interval = setInterval(() => {
      setFiles(prev => prev.map(f => {
        if (f.id === fileId) {
          const newProgress = Math.min(f.progress + Math.random() * 20, 100)
          if (newProgress >= 100) {
            clearInterval(interval)
            return { ...f, progress: 100, status: 'processing' }
          }
          return { ...f, progress: newProgress }
        }
        return f
      }))
    }, 200)
  }

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = (type: string) => {
    if (type.startsWith('video/')) {
      return <FileVideo className="w-8 h-8 text-blue-500" />
    } else if (type.startsWith('audio/')) {
      return <FileAudio className="w-8 h-8 text-green-500" />
    }
    return <FileVideo className="w-8 h-8 text-gray-500" />
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploading':
        return 'bg-blue-100 text-blue-800'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'uploading':
        return 'Uploading...'
      case 'processing':
        return 'Processing...'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      default:
        return 'Unknown'
    }
  }

  const startTranscription = () => {
    if (files.length === 0) return

    // In production, this would send the files and settings to the backend
    console.log('Starting transcription with settings:', settings)
    console.log('Files:', files)

    // Simulate starting transcription
    setFiles(prev => prev.map(f => ({ ...f, status: 'processing' })))
  }

  const supportedFormats = [
    'Video: MP4, MOV, AVI, WMV, FLV, WebM',
    'Audio: MP3, WAV, M4A, FLAC, OGG, AAC',
    'Maximum file size: 2GB per file',
    'Maximum duration: 4 hours per file'
  ]

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Link
              href="/transcripts"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              ← Back to Transcripts
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-foreground">Upload Media</h1>
          <p className="text-muted-foreground mt-2">
            Upload audio or video files to create transcripts
          </p>
        </div>

        {/* Settings Panel */}
        <div className="mb-8">
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5" />
              <h2 className="text-lg font-semibold">Transcription Settings</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Language</label>
                <select
                  value={settings.language}
                  onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value }))}
                  className="w-full p-2 border rounded-md bg-background"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="it">Italian</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Quality</label>
                <select
                  value={settings.quality}
                  onChange={(e) => setSettings(prev => ({ ...prev, quality: e.target.value as any }))}
                  className="w-full p-2 border rounded-md bg-background"
                >
                  <option value="standard">Standard</option>
                  <option value="high">High</option>
                  <option value="premium">Premium</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="diarization"
                  checked={settings.enableDiarization}
                  onChange={(e) => setSettings(prev => ({ ...prev, enableDiarization: e.target.checked }))}
                  className="rounded"
                />
                <label htmlFor="diarization" className="text-sm">Speaker Diarization</label>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="wordTiming"
                  checked={settings.enableWordTiming}
                  onChange={(e) => setSettings(prev => ({ ...prev, enableWordTiming: e.target.checked }))}
                  className="rounded"
                />
                <label htmlFor="wordTiming" className="text-sm">Word-level Timing</label>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="customDict"
                  checked={settings.customDictionary}
                  onChange={(e) => setSettings(prev => ({ ...prev, customDictionary: e.target.checked }))}
                  className="rounded"
                />
                <label htmlFor="customDict" className="text-sm">Custom Dictionary</label>
              </div>
            </div>
          </div>
        </div>

        {/* Upload Area */}
        <div className="mb-8">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">Drop files here or click to browse</h3>
            <p className="text-muted-foreground mb-4">
              Support for video and audio files up to 2GB
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
            >
              Choose Files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="video/*,audio/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Uploaded Files</h2>
              <button
                onClick={startTranscription}
                disabled={files.some(f => f.status === 'uploading')}
                className="bg-primary text-primary-foreground px-6 py-2 rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Start Transcription
              </button>
            </div>

            <div className="space-y-4">
              {files.map((file) => (
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-card border rounded-lg p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {getFileIcon(file.type)}
                      <div>
                        <h4 className="font-medium">{file.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {formatFileSize(file.size)} • {file.type}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(file.status)}`}>
                          {getStatusText(file.status)}
                        </div>
                        {file.status === 'uploading' && (
                          <div className="text-sm text-muted-foreground mt-1">
                            {file.progress.toFixed(0)}%
                          </div>
                        )}
                      </div>

                      <button
                        onClick={() => removeFile(file.id)}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {file.status === 'uploading' && (
                    <div className="mt-4">
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {file.error && (
                    <div className="mt-4 flex items-center space-x-2 text-destructive">
                      <AlertCircle className="w-4 h-4" />
                      <span className="text-sm">{file.error}</span>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Supported Formats */}
        <div className="bg-muted/50 rounded-lg p-6">
          <h3 className="font-medium mb-3">Supported Formats</h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {supportedFormats.map((format, index) => (
              <li key={index} className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                <span>{format}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
