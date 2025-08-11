"use client"

import React, { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Search, Filter, Plus, Play, Download, Edit, Clock, User, Calendar } from 'lucide-react'
import { Transcript, Matter } from '@/types'

// Sample data for development
const sampleTranscripts: Transcript[] = [
  {
    id: '1',
    matterId: 'matter-1',
    title: 'Court Hearing - Smith vs. Johnson',
    language: 'en',
    asrModel: 'faster-whisper-large-v3',
    diarizationModel: 'pyannote-2.1',
    totalDurationMs: 1265323,
    version: 1,
    encrypted: false,
    segments: [],
    speakerMap: {},
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    matterId: 'matter-2',
    title: 'Deposition - Dr. Emily Rodriguez',
    language: 'en',
    asrModel: 'faster-whisper-large-v3',
    diarizationModel: 'pyannote-2.1',
    totalDurationMs: 1800000,
    version: 1,
    encrypted: false,
    segments: [],
    speakerMap: {},
    createdAt: '2024-01-14T14:30:00Z',
    updatedAt: '2024-01-14T14:30:00Z'
  },
  {
    id: '3',
    matterId: 'matter-3',
    title: 'Police Interview - Witness Statement',
    language: 'en',
    asrModel: 'faster-whisper-large-v3',
    diarizationModel: 'pyannote-2.1',
    totalDurationMs: 900000,
    version: 1,
    encrypted: false,
    segments: [],
    speakerMap: {},
    createdAt: '2024-01-13T09:15:00Z',
    updatedAt: '2024-01-13T09:15:00Z'
  }
]

const sampleMatters: Record<string, Matter> = {
  'matter-1': {
    id: 'matter-1',
    title: 'Smith vs. Johnson',
    status: 'active',
    priority: 'high',
    practiceArea: 'Personal Injury',
    clientName: 'Sarah Smith',
    retentionDays: 90,
    storeMedia: true,
    storeTranscripts: true,
    allowAnonLearning: false,
    customFields: {},
    createdAt: '2024-01-10T00:00:00Z',
    updatedAt: '2024-01-15T00:00:00Z'
  },
  'matter-2': {
    id: 'matter-2',
    title: 'Corporate Litigation - TechCorp',
    status: 'active',
    priority: 'medium',
    practiceArea: 'Corporate Law',
    clientName: 'TechCorp Inc.',
    retentionDays: 180,
    storeMedia: true,
    storeTranscripts: true,
    allowAnonLearning: false,
    customFields: {},
    createdAt: '2024-01-05T00:00:00Z',
    updatedAt: '2024-01-14T00:00:00Z'
  },
  'matter-3': {
    id: 'matter-3',
    title: 'Criminal Defense - State v. Davis',
    status: 'active',
    priority: 'urgent',
    practiceArea: 'Criminal Law',
    clientName: 'Michael Davis',
    retentionDays: 365,
    storeMedia: true,
    storeTranscripts: true,
    allowAnonLearning: false,
    customFields: {},
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-13T00:00:00Z'
  }
}

export default function TranscriptsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [matterFilter, setMatterFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'duration'>('date')

  const formatDuration = (ms: number) => {
    const minutes = Math.floor(ms / 60000)
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60

    if (hours > 0) {
      return `${hours}h ${remainingMinutes}m`
    }
    return `${minutes}m`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const filteredTranscripts = sampleTranscripts.filter(transcript => {
    const matchesSearch = transcript.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         sampleMatters[transcript.matterId]?.title.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus = statusFilter === 'all' || true // All transcripts are ready for now
    const matchesMatter = matterFilter === 'all' || transcript.matterId === matterFilter

    return matchesSearch && matchesStatus && matchesMatter
  })

  const sortedTranscripts = [...filteredTranscripts].sort((a, b) => {
    switch (sortBy) {
      case 'title':
        return (a.title || '').localeCompare(b.title || '')
      case 'duration':
        return b.totalDurationMs - a.totalDurationMs
      case 'date':
      default:
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    }
  })

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Transcripts</h1>
            <p className="text-muted-foreground mt-2">
              Manage and edit your legal transcripts
            </p>
          </div>

          <Link
            href="/transcripts/upload"
            className="flex items-center space-x-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>Upload Media</span>
          </Link>
        </div>

        {/* Filters and Search */}
        <div className="bg-card rounded-lg border p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                placeholder="Search transcripts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            {/* Matter Filter */}
            <select
              value={matterFilter}
              onChange={(e) => setMatterFilter(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="all">All Matters</option>
              {Object.values(sampleMatters).map(matter => (
                <option key={matter.id} value={matter.id}>
                  {matter.title}
                </option>
              ))}
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value="ready">Ready</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>

            {/* Sort By */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="date">Sort by Date</option>
              <option value="title">Sort by Title</option>
              <option value="duration">Sort by Duration</option>
            </select>
          </div>
        </div>

        {/* Transcripts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedTranscripts.map((transcript, index) => {
            const matter = sampleMatters[transcript.matterId]

            return (
              <motion.div
                key={transcript.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-card rounded-lg border hover:shadow-lg transition-all duration-200"
              >
                {/* Transcript Header */}
                <div className="p-6 border-b">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-foreground line-clamp-2 mb-2">
                        {transcript.title || 'Untitled Transcript'}
                      </h3>
                      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                        <User className="w-4 h-4" />
                        <span>{matter?.clientName || 'Unknown Client'}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                        Ready
                      </span>
                    </div>
                  </div>

                  {/* Matter Info */}
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                        {matter?.practiceArea || 'Unknown'}
                      </span>
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">
                        {matter?.priority || 'Unknown'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Transcript Details */}
                <div className="p-6 space-y-4">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2 text-muted-foreground">
                      <Clock className="w-4 h-4" />
                      <span>{formatDuration(transcript.totalDurationMs)}</span>
                    </div>

                    <div className="flex items-center space-x-2 text-muted-foreground">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(transcript.createdAt)}</span>
                    </div>
                  </div>

                  <div className="text-sm text-muted-foreground">
                    <div>Model: {transcript.asrModel}</div>
                    <div>Language: {transcript.language.toUpperCase()}</div>
                    <div>Version: {transcript.version}</div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 pt-4">
                    <Link
                      href={`/transcripts/${transcript.id}`}
                      className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      <span>Open Editor</span>
                    </Link>

                    <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors">
                      <Download className="w-4 h-4" />
                    </button>

                    <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors">
                      <Edit className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Empty State */}
        {sortedTranscripts.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <div className="w-24 h-24 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-12 h-12 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No transcripts found</h3>
            <p className="text-muted-foreground mb-6">
              {searchQuery || statusFilter !== 'all' || matterFilter !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Get started by uploading your first media file'
              }
            </p>
            {!searchQuery && statusFilter === 'all' && matterFilter === 'all' && (
              <Link
                href="/transcripts/upload"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Plus className="w-5 h-5" />
                <span>Upload Media</span>
              </Link>
            )}
          </motion.div>
        )}
      </div>
    </div>
  )
}
