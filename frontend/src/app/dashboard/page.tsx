"use client"

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  FileText,
  Play,
  Clock,
  TrendingUp,
  Users,
  Calendar,
  BarChart3,
  Activity,
  Plus,
  ArrowRight,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react'

interface DashboardStats {
  totalTranscripts: number
  totalMatters: number
  totalDuration: number
  averageConfidence: number
  recentActivity: number
}

interface RecentTranscript {
  id: string
  title: string
  matterTitle: string
  duration: number
  status: 'completed' | 'processing' | 'failed'
  createdAt: string
}

interface RecentMatter {
  id: string
  title: string
  clientName: string
  practiceArea: string
  transcriptCount: number
  lastActivity: string
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalTranscripts: 0,
    totalMatters: 0,
    totalDuration: 0,
    averageConfidence: 0,
    recentActivity: 0
  })

  const [recentTranscripts, setRecentTranscripts] = useState<RecentTranscript[]>([])
  const [recentMatters, setRecentMatters] = useState<RecentMatter[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Simulate loading data
  useEffect(() => {
    const loadDashboardData = async () => {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000))

      setStats({
        totalTranscripts: 24,
        totalMatters: 8,
        totalDuration: 156000000, // 43.3 hours in ms
        averageConfidence: 0.89,
        recentActivity: 12
      })

      setRecentTranscripts([
        {
          id: '1',
          title: 'Court Hearing - Smith vs. Johnson',
          matterTitle: 'Smith vs. Johnson',
          duration: 1265323,
          status: 'completed',
          createdAt: '2024-01-15T10:00:00Z'
        },
        {
          id: '2',
          title: 'Deposition - Dr. Emily Rodriguez',
          matterTitle: 'Corporate Litigation - TechCorp',
          duration: 1800000,
          status: 'processing',
          createdAt: '2024-01-14T14:30:00Z'
        },
        {
          id: '3',
          title: 'Police Interview - Witness Statement',
          matterTitle: 'Criminal Defense - State v. Davis',
          duration: 900000,
          status: 'completed',
          createdAt: '2024-01-13T09:15:00Z'
        },
        {
          id: '4',
          title: 'Client Consultation - Estate Planning',
          matterTitle: 'Estate Planning - Johnson Family',
          duration: 1200000,
          status: 'failed',
          createdAt: '2024-01-12T16:45:00Z'
        }
      ])

      setRecentMatters([
        {
          id: '1',
          title: 'Smith vs. Johnson',
          clientName: 'Sarah Smith',
          practiceArea: 'Personal Injury',
          transcriptCount: 3,
          lastActivity: '2024-01-15T10:00:00Z'
        },
        {
          id: '2',
          title: 'Corporate Litigation - TechCorp',
          clientName: 'TechCorp Inc.',
          practiceArea: 'Corporate Law',
          transcriptCount: 2,
          lastActivity: '2024-01-14T14:30:00Z'
        },
        {
          id: '3',
          title: 'Criminal Defense - State v. Davis',
          clientName: 'Michael Davis',
          practiceArea: 'Criminal Law',
          transcriptCount: 1,
          lastActivity: '2024-01-13T09:15:00Z'
        }
      ])

      setIsLoading(false)
    }

    loadDashboardData()
  }, [])

  const formatDuration = (ms: number) => {
    const hours = Math.floor(ms / 3600000)
    const minutes = Math.floor((ms % 3600000) / 60000)

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Welcome back! Here's what's happening with your cases.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-card rounded-lg border p-6"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Transcripts</p>
                <p className="text-2xl font-bold text-foreground">{stats.totalTranscripts}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-card rounded-lg border p-6"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Matters</p>
                <p className="text-2xl font-bold text-foreground">{stats.totalMatters}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-card rounded-lg border p-6"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Clock className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Duration</p>
                <p className="text-2xl font-bold text-foreground">{formatDuration(stats.totalDuration)}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-card rounded-lg border p-6"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-orange-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg Confidence</p>
                <p className="text-2xl font-bold text-foreground">{(stats.averageConfidence * 100).toFixed(0)}%</p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-card rounded-lg border p-6 mb-8"
        >
          <h2 className="text-lg font-semibold text-foreground mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/transcripts/upload"
              className="flex items-center space-x-3 p-4 border rounded-lg hover:bg-muted transition-colors"
            >
              <div className="p-2 bg-blue-100 rounded-lg">
                <Plus className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-foreground">Upload Media</p>
                <p className="text-sm text-muted-foreground">Start a new transcription</p>
              </div>
            </Link>

            <Link
              href="/transcripts"
              className="flex items-center space-x-3 p-4 border rounded-lg hover:bg-muted transition-colors"
            >
              <div className="p-2 bg-green-100 rounded-lg">
                <FileText className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="font-medium text-foreground">View Transcripts</p>
                <p className="text-sm text-muted-foreground">Browse all transcripts</p>
              </div>
            </Link>

            <Link
              href="/matters"
              className="flex items-center space-x-3 p-4 border rounded-lg hover:bg-muted transition-colors"
            >
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="font-medium text-foreground">Manage Matters</p>
                <p className="text-sm text-muted-foreground">Organize your cases</p>
              </div>
            </Link>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Transcripts */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-card rounded-lg border p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Recent Transcripts</h2>
              <Link
                href="/transcripts"
                className="text-sm text-primary hover:text-primary/80 transition-colors flex items-center space-x-1"
              >
                <span>View all</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="space-y-4">
              {recentTranscripts.map((transcript) => (
                <div key={transcript.id} className="flex items-center space-x-4 p-3 border rounded-lg">
                  {getStatusIcon(transcript.status)}

                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground truncate">
                      {transcript.title}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {transcript.matterTitle} • {formatDuration(transcript.duration)}
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(transcript.status)}`}>
                      {transcript.status}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(transcript.createdAt)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Recent Matters */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-card rounded-lg border p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Recent Matters</h2>
              <Link
                href="/matters"
                className="text-sm text-primary hover:text-primary/80 transition-colors flex items-center space-x-1"
              >
                <span>View all</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="space-y-4">
              {recentMatters.map((matter) => (
                <div key={matter.id} className="flex items-center space-x-4 p-3 border rounded-lg">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Users className="w-4 h-4 text-blue-600" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground truncate">
                      {matter.title}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {matter.clientName} • {matter.practiceArea}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-sm font-medium text-foreground">
                      {matter.transcriptCount} transcripts
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(matter.lastActivity)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Activity Chart Placeholder */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-card rounded-lg border p-6 mt-8"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">Activity Overview</h2>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">Last 30 days</span>
              <BarChart3 className="w-4 h-4 text-muted-foreground" />
            </div>
          </div>

          <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
            <div className="text-center">
              <Activity className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
              <p className="text-muted-foreground">Activity chart coming soon</p>
              <p className="text-sm text-muted-foreground">Track your transcription activity over time</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
