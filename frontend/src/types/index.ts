// Core types for CasePrep application

export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  role: UserRole
  tenantId: string
  createdAt: string
}

export type UserRole = 'owner' | 'admin' | 'member' | 'viewer'

export interface Tenant {
  id: string
  name: string
  plan: SubscriptionPlan
  createdAt: string
  settings: TenantSettings
}

export type SubscriptionPlan = 'starter' | 'professional' | 'enterprise'

export interface TenantSettings {
  dataRetentionDays: number
  requireMfa: boolean
  allowedIpRanges: string[]
  autoTranscription: boolean
  defaultLanguage: string
  transcriptionQuality: 'standard' | 'high' | 'premium'
}

export interface Matter {
  id: string
  title: string
  description?: string
  caseNumber?: string
  clientName?: string
  status: MatterStatus
  priority: MatterPriority
  practiceArea?: string
  courtName?: string
  judgeName?: string
  statuteOfLimitations?: string
  trialDate?: string
  discoveryDeadline?: string
  retentionDays: number
  storeMedia: boolean
  storeTranscripts: boolean
  allowAnonLearning: boolean
  billingRate?: number
  estimatedValue?: number
  budgetLimit?: number
  customFields: Record<string, any>
  createdAt: string
  updatedAt: string
}

export type MatterStatus = 'active' | 'closed' | 'pending' | 'archived'
export type MatterPriority = 'low' | 'medium' | 'high' | 'urgent'

export interface MediaAsset {
  id: string
  matterId: string
  filename: string
  mimeType: string
  byteLength: number
  sha256: string
  storageUri?: string
  status: MediaStatus
  type: MediaType
  durationMs?: number
  width?: number
  height?: number
  createdAt: string
}

export type MediaStatus = 'uploading' | 'processing' | 'ready' | 'failed'
export type MediaType = 'video' | 'audio' | 'document' | 'image'

export interface Transcript {
  id: string
  matterId: string
  mediaId?: string
  title?: string
  language: string
  diarizationModel?: string
  asrModel: string
  totalDurationMs: number
  version: number
  encrypted: boolean
  segments: TranscriptSegment[]
  speakerMap: Record<string, string>
  mediaUrl?: string
  createdAt: string
  updatedAt: string
}

export interface TranscriptSegment {
  id: string
  transcriptId: string
  speaker: string
  startMs: number
  endMs: number
  text: string
  confidence?: number
  words?: Word[]
  createdAt: string
}

export interface Word {
  word: string
  startMs: number
  endMs: number
  confidence: number
}

export type TranscriptStatus = 'processing' | 'ready' | 'failed' | 'archived'
export type TranscriptFormat = 'srt' | 'vtt' | 'docx' | 'pdf' | 'csv' | 'json'

export interface SpeakerRole {
  id: string
  transcriptId: string
  placeholder: string
  alias: string
  createdAt: string
}

export interface UserDictionary {
  id: string
  userId: string
  pattern: string
  replacement: string
  scope: 'word' | 'phrase' | 'regex'
  isActive: boolean
  createdAt: string
}

export interface AuditEvent {
  id: string
  transcriptId: string
  eventType: string
  eventPayload: Record<string, any>
  eventTime: string
  prevHash?: string
  currHash: string
}

export interface TranscriptionJob {
  id: string
  matterId: string
  mediaId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
  createdAt: string
  updatedAt: string
}

export interface ExportOptions {
  format: TranscriptFormat
  includeMetadata: boolean
  includeConfidence: boolean
  includeSpeakerMapping: boolean
  includeTimestamps: boolean
  includeWords: boolean
}

export interface ClipRequest {
  transcriptId: string
  startMs: number
  endMs: number
  title?: string
  description?: string
  includeVideo: boolean
  includeAudio: boolean
  includeTranscript: boolean
}

export interface Clip {
  id: string
  transcriptId: string
  title: string
  description?: string
  startMs: number
  endMs: number
  durationMs: number
  mediaUrl?: string
  transcriptText: string
  createdAt: string
}

// API Response types
export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
}

export interface ApiError {
  message: string
  code: string
  details?: Record<string, any>
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

// Form types
export interface CreateMatterForm {
  title: string
  description?: string
  caseNumber?: string
  clientName?: string
  retentionDays: number
  storeMedia: boolean
  storeTranscripts: boolean
  allowAnonymousLearning: boolean
}

export interface UploadMediaForm {
  matterId: string
  files: File[]
  processImmediately: boolean
}

export interface TranscriptSettingsForm {
  language: string
  enableDiarization: boolean
  customDictionary: string[]
  confidenceThreshold: number
}

// UI State types
export interface UiState {
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  notifications: Notification[]
  loading: boolean
  error?: string
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
  actions?: NotificationAction[]
}

export interface NotificationAction {
  label: string
  action: () => void
  variant?: 'default' | 'destructive'
}

// WebSocket types
export interface WebSocketMessage {
  type: string
  payload: any
  timestamp: string
}

export interface TranscriptProgressMessage extends WebSocketMessage {
  type: 'transcript_progress'
  payload: {
    transcriptId: string
    status: TranscriptStatus
    progress: number
    currentStep: string
    error?: string
  }
}

// File upload types
export interface UploadProgress {
  fileId: string
  filename: string
  progress: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
}

// Search and filtering types
export interface SearchFilters {
  query?: string
  matterId?: string
  status?: TranscriptStatus[]
  dateRange?: {
    start: string
    end: string
  }
  duration?: {
    min: number
    max: number
  }
  speakers?: {
    min: number
    max: number
  }
}

export interface SortOption {
  field: string
  direction: 'asc' | 'desc'
  label: string
}

// Player types
export interface PlayerState {
  playing: boolean
  currentTime: number
  duration: number
  volume: number
  muted: boolean
  playbackRate: number
  seeking: boolean
}

export interface PlayerControls {
  play: () => void
  pause: () => void
  seekTo: (time: number) => void
  setVolume: (volume: number) => void
  setPlaybackRate: (rate: number) => void
  toggleMute: () => void
}

// Analytics types
export interface UsageStats {
  totalTranscripts: number
  totalDurationMs: number
  averageDurationMs: number
  completionRate: number
  mostActiveDay: string
  topSpeakerCount: number
  languageDistribution: Record<string, number>
  monthlyUsage: Array<{
    month: string
    count: number
    durationMs: number
  }>
}

// Theme types
export interface ThemeConfig {
  primary: string
  secondary: string
  accent: string
  background: string
  foreground: string
  muted: string
  border: string
}

export interface AccessibilitySettings {
  reducedMotion: boolean
  highContrast: boolean
  fontSize: 'small' | 'medium' | 'large' | 'extra-large'
  screenReaderOptimized: boolean
}