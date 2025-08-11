// Core types for CasePrep application

export interface User {
  id: string
  email: string
  displayName: string
  role: UserRole
  tenantId: string
  createdAt: string
  lastLoginAt?: string
  avatar?: string
}

export type UserRole = 'owner' | 'admin' | 'editor' | 'viewer'

export interface Tenant {
  id: string
  name: string
  plan: SubscriptionPlan
  createdAt: string
  settings: TenantSettings
}

export type SubscriptionPlan = 'starter' | 'professional' | 'enterprise'

export interface TenantSettings {
  retentionDays: number
  allowAnonymousLearning: boolean
  requireTwoFactor: boolean
  customBranding?: {
    logo?: string
    primaryColor?: string
    secondaryColor?: string
  }
}

export interface Matter {
  id: string
  tenantId: string
  title: string
  description?: string
  caseNumber?: string
  clientName?: string
  status: MatterStatus
  retentionDays: number
  storeMedia: boolean
  storeTranscripts: boolean
  allowAnonymousLearning: boolean
  createdAt: string
  updatedAt: string
  transcriptCount: number
  totalDurationMs: number
}

export type MatterStatus = 'active' | 'archived' | 'closed'

export interface MediaAsset {
  id: string
  matterId: string
  filename: string
  originalFilename: string
  mimeType: string
  fileSize: number
  durationMs?: number
  sha256: string
  storageUri?: string
  thumbnailUri?: string
  createdAt: string
  uploadedBy: string
}

export interface Transcript {
  id: string
  matterId: string
  mediaId: string
  title: string
  language: string
  status: TranscriptStatus
  progress: number
  diarizationModel?: string
  asrModel?: string
  totalDurationMs: number
  segmentCount: number
  speakerCount: number
  version: number
  encrypted: boolean
  createdAt: string
  updatedAt: string
  completedAt?: string
  error?: string
  
  // Populated relations
  media?: MediaAsset
  matter?: Matter
  segments?: TranscriptSegment[]
  speakerMap?: SpeakerAlias[]
}

export type TranscriptStatus = 
  | 'pending'
  | 'processing' 
  | 'completed'
  | 'failed'
  | 'cancelled'

export interface TranscriptSegment {
  id: string
  transcriptId: string
  speakerLabel: string
  startMs: number
  endMs: number
  text: string
  confidence: number
  words?: WordTiming[]
  edited: boolean
  createdAt: string
}

export interface WordTiming {
  word: string
  startMs: number
  endMs: number
  confidence: number
}

export interface SpeakerAlias {
  id: string
  transcriptId: string
  placeholder: string
  alias: string
  createdAt: string
}

export interface TranscriptEdit {
  id: string
  transcriptId: string
  userId: string
  segmentId: string
  beforeText: string
  afterText: string
  editType: EditType
  createdAt: string
}

export type EditType = 'text_correction' | 'speaker_change' | 'timing_adjustment'

export interface UserDictionary {
  id: string
  userId: string
  pattern: string
  replacement: string
  scope: DictionaryScope
  isActive: boolean
  usageCount: number
  createdAt: string
}

export type DictionaryScope = 'exact' | 'word' | 'regex'

export interface AuditEvent {
  id: string
  transcriptId: string
  eventType: AuditEventType
  eventPayload: Record<string, any>
  eventTime: string
  userId?: string
  prevHash?: string
  currHash: string
}

export type AuditEventType = 
  | 'upload'
  | 'process_start'
  | 'process_complete'
  | 'edit'
  | 'export'
  | 'delete'
  | 'view'

export interface ExportRequest {
  id: string
  transcriptId: string
  format: ExportFormat
  options: ExportOptions
  status: ExportStatus
  downloadUrl?: string
  error?: string
  createdAt: string
  completedAt?: string
  expiresAt?: string
}

export type ExportFormat = 'srt' | 'vtt' | 'docx' | 'pdf' | 'csv' | 'json'

export type ExportStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'expired'

export interface ExportOptions {
  includeTimestamps?: boolean
  includeSpeakers?: boolean
  includeConfidence?: boolean
  speakerFormat?: 'label' | 'alias'
  timestampFormat?: 'ms' | 'seconds' | 'timecode'
  pageFormat?: 'a4' | 'letter'
  fontSize?: number
  includeAuditTrail?: boolean
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