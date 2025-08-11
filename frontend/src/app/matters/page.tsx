"use client"

import React, { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  Search,
  Filter,
  Plus,
  Users,
  Calendar,
  Clock,
  FileText,
  MoreVertical,
  Edit,
  Trash2,
  Eye,
  Settings,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react'

interface Matter {
  id: string
  title: string
  status: 'active' | 'closed' | 'pending'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  practiceArea: string
  clientName: string
  retentionDays: number
  storeMedia: boolean
  storeTranscripts: boolean
  allowAnonLearning: boolean
  customFields: Record<string, any>
  createdAt: string
  updatedAt: string
  transcriptCount: number
  totalDuration: number
}

const sampleMatters: Matter[] = [
  {
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
    customFields: {
      caseNumber: '2024-CV-001234',
      court: 'Superior Court of California',
      judge: 'Hon. Sarah Williams'
    },
    createdAt: '2024-01-10T00:00:00Z',
    updatedAt: '2024-01-15T00:00:00Z',
    transcriptCount: 3,
    totalDuration: 1265323
  },
  {
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
    customFields: {
      caseNumber: '2024-CV-005678',
      court: 'Federal District Court',
      judge: 'Hon. Michael Chen'
    },
    createdAt: '2024-01-05T00:00:00Z',
    updatedAt: '2024-01-14T00:00:00Z',
    transcriptCount: 2,
    totalDuration: 1800000
  },
  {
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
    customFields: {
      caseNumber: '2024-CR-009876',
      court: 'Superior Court of California',
      judge: 'Hon. Robert Johnson'
    },
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-13T00:00:00Z',
    transcriptCount: 1,
    totalDuration: 900000
  },
  {
    id: 'matter-4',
    title: 'Estate Planning - Johnson Family',
    status: 'pending',
    priority: 'low',
    practiceArea: 'Estate Planning',
    clientName: 'Johnson Family Trust',
    retentionDays: 2555, // 7 years
    storeMedia: false,
    storeTranscripts: true,
    allowAnonLearning: true,
    customFields: {
      trustNumber: 'JT-2024-001',
      trustee: 'Sarah Johnson'
    },
    createdAt: '2024-01-08T00:00:00Z',
    updatedAt: '2024-01-12T00:00:00Z',
    transcriptCount: 0,
    totalDuration: 0
  },
  {
    id: 'matter-5',
    title: 'Employment Dispute - Martinez',
    status: 'closed',
    priority: 'medium',
    practiceArea: 'Employment Law',
    clientName: 'Maria Martinez',
    retentionDays: 90,
    storeMedia: false,
    storeTranscripts: true,
    allowAnonLearning: false,
    customFields: {
      caseNumber: '2023-EMP-004321',
      settlement: 'Confidential'
    },
    createdAt: '2023-06-15T00:00:00Z',
    updatedAt: '2023-12-20T00:00:00Z',
    transcriptCount: 2,
    totalDuration: 2400000
  }
]

export default function MattersPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')
  const [practiceAreaFilter, setPracticeAreaFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'priority' | 'status'>('date')

  const formatDuration = (ms: number) => {
    if (ms === 0) return '0m'
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
      day: 'numeric'
    })
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800'
      case 'high':
        return 'bg-orange-100 text-orange-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'closed':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'closed':
        return <XCircle className="w-4 h-4 text-gray-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const filteredMatters = sampleMatters.filter(matter => {
    const matchesSearch = matter.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         matter.clientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         matter.practiceArea.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus = statusFilter === 'all' || matter.status === statusFilter
    const matchesPriority = priorityFilter === 'all' || matter.priority === priorityFilter
    const matchesPracticeArea = practiceAreaFilter === 'all' || matter.practiceArea === practiceAreaFilter

    return matchesSearch && matchesStatus && matchesPriority && matchesPracticeArea
  })

  const sortedMatters = [...filteredMatters].sort((a, b) => {
    switch (sortBy) {
      case 'title':
        return a.title.localeCompare(b.title)
      case 'priority':
        const priorityOrder = { 'urgent': 4, 'high': 3, 'medium': 2, 'low': 1 }
        return priorityOrder[b.priority as keyof typeof priorityOrder] - priorityOrder[a.priority as keyof typeof priorityOrder]
      case 'status':
        return a.status.localeCompare(b.status)
      case 'date':
      default:
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    }
  })

  const practiceAreas = Array.from(new Set(sampleMatters.map(m => m.practiceArea)))

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Matters</h1>
            <p className="text-muted-foreground mt-2">
              Manage your legal cases and matters
            </p>
          </div>

          <Link
            href="/matters/new"
            className="flex items-center space-x-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>New Matter</span>
          </Link>
        </div>

        {/* Filters and Search */}
        <div className="bg-card rounded-lg border p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                placeholder="Search matters..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="closed">Closed</option>
            </select>

            {/* Priority Filter */}
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="all">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {/* Practice Area Filter */}
            <select
              value={practiceAreaFilter}
              onChange={(e) => setPracticeAreaFilter(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="all">All Practice Areas</option>
              {practiceAreas.map(area => (
                <option key={area} value={area}>{area}</option>
              ))}
            </select>

            {/* Sort By */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="date">Sort by Date</option>
              <option value="title">Sort by Title</option>
              <option value="priority">Sort by Priority</option>
              <option value="status">Sort by Status</option>
            </select>
          </div>
        </div>

        {/* Matters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedMatters.map((matter, index) => (
            <motion.div
              key={matter.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-card rounded-lg border hover:shadow-lg transition-all duration-200"
            >
              {/* Matter Header */}
              <div className="p-6 border-b">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground line-clamp-2 mb-2">
                      {matter.title}
                    </h3>
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <Users className="w-4 h-4" />
                      <span>{matter.clientName}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(matter.status)}`}>
                      {matter.status}
                    </span>
                  </div>
                </div>

                {/* Matter Info */}
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                      {matter.practiceArea}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(matter.priority)}`}>
                      {matter.priority}
                    </span>
                  </div>
                </div>
              </div>

              {/* Matter Details */}
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2 text-muted-foreground">
                    <FileText className="w-4 h-4" />
                    <span>{matter.transcriptCount} transcripts</span>
                  </div>

                  <div className="flex items-center space-x-2 text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    <span>{formatDuration(matter.totalDuration)}</span>
                  </div>
                </div>

                <div className="text-sm text-muted-foreground">
                  <div>Retention: {matter.retentionDays} days</div>
                  <div>Media Storage: {matter.storeMedia ? 'Enabled' : 'Disabled'}</div>
                  <div>Transcript Storage: {matter.storeTranscripts ? 'Enabled' : 'Disabled'}</div>
                  <div>Anonymous Learning: {matter.allowAnonLearning ? 'Allowed' : 'Blocked'}</div>
                </div>

                {/* Custom Fields */}
                {Object.keys(matter.customFields).length > 0 && (
                  <div className="pt-2 border-t">
                    <div className="text-xs font-medium text-muted-foreground mb-2">Case Details</div>
                    <div className="space-y-1">
                      {Object.entries(matter.customFields).map(([key, value]) => (
                        <div key={key} className="text-xs text-muted-foreground">
                          <span className="font-medium">{key}:</span> {value}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center space-x-2 pt-4">
                  <Link
                    href={`/matters/${matter.id}`}
                    className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    <span>View Details</span>
                  </Link>

                  <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors">
                    <Edit className="w-4 h-4" />
                  </button>

                  <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Empty State */}
        {sortedMatters.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <div className="w-24 h-24 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-12 h-12 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No matters found</h3>
            <p className="text-muted-foreground mb-6">
              {searchQuery || statusFilter !== 'all' || priorityFilter !== 'all' || practiceAreaFilter !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Get started by creating your first matter'
              }
            </p>
            {!searchQuery && statusFilter === 'all' && priorityFilter === 'all' && practiceAreaFilter === 'all' && (
              <Link
                href="/matters/new"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Plus className="w-5 h-5" />
                <span>Create Matter</span>
              </Link>
            )}
          </motion.div>
        )}
      </div>
    </div>
  )
}
