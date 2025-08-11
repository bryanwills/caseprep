"use client"

import React, { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TranscriptSegment, Transcript } from '@/types'
import { TranscriptPlayer } from './TranscriptPlayer'
import { TranscriptTimeline } from './TranscriptTimeline'
import { TranscriptControls } from './TranscriptControls'
import { ExportDialog } from './ExportDialog'
import { SpeakerMapping } from './SpeakerMapping'
import { DictionaryEditor } from './DictionaryEditor'

interface TranscriptEditorProps {
  transcript: Transcript
  onTranscriptUpdate: (transcript: Transcript) => void
  onExport: (format: string) => void
}

export function TranscriptEditor({
  transcript,
  onTranscriptUpdate,
  onExport
}: TranscriptEditorProps) {
  const [currentTime, setCurrentTime] = useState(0)
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [showSpeakerMapping, setShowSpeakerMapping] = useState(false)
  const [showDictionary, setShowDictionary] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const videoRef = useRef<HTMLVideoElement>(null)
  const transcriptRef = useRef<HTMLDivElement>(null)

  // Sync video time with transcript
  useEffect(() => {
    if (videoRef.current) {
      const handleTimeUpdate = () => {
        setCurrentTime(videoRef.current?.currentTime || 0)
      }

      videoRef.current.addEventListener('timeupdate', handleTimeUpdate)
      return () => {
        videoRef.current?.removeEventListener('timeupdate', handleTimeUpdate)
      }
    }
    return undefined
  }, [])

  // Seek to segment when clicked
  const seekToSegment = (startTime: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = startTime / 1000
      setIsPlaying(true)
    }
  }

  // Update segment text
  const updateSegmentText = (segmentId: string, newText: string) => {
    const updatedTranscript = {
      ...transcript,
      segments: transcript.segments.map(segment =>
        segment.id === segmentId
          ? { ...segment, text: newText }
          : segment
      )
    }
    onTranscriptUpdate(updatedTranscript)
  }

  // Update speaker labels
  const updateSpeakerLabel = (oldLabel: string, newLabel: string) => {
    const updatedTranscript = {
      ...transcript,
      segments: transcript.segments.map(segment =>
        segment.speaker === oldLabel
          ? { ...segment, speaker: newLabel }
          : segment
      ),
      speakerMap: {
        ...transcript.speakerMap,
        [oldLabel]: newLabel
      }
    }
    onTranscriptUpdate(updatedTranscript)
  }

  // Filter segments based on search
  const filteredSegments = transcript.segments.filter(segment =>
    segment.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
    segment.speaker.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header Controls */}
      <div className="flex items-center justify-between p-4 border-b bg-card">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-semibold text-foreground">
            {transcript.title || 'Transcript Editor'}
          </h1>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSpeakerMapping(true)}
              className="px-3 py-1.5 text-sm bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80"
            >
              Speaker Mapping
            </button>
            <button
              onClick={() => setShowDictionary(true)}
              className="px-3 py-1.5 text-sm bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80"
            >
              Dictionary
            </button>
            <button
              onClick={() => setEditMode(!editMode)}
              className={`px-3 py-1.5 text-sm rounded-md ${
                editMode
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground'
              }`}
            >
              {editMode ? 'View Mode' : 'Edit Mode'}
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Search transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded-md bg-background text-foreground placeholder:text-muted-foreground"
          />
          <button
            onClick={() => setShowExportDialog(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Export
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Media Player */}
        <div className="w-full lg:w-3/5 p-4">
          {transcript.mediaUrl ? (
            <TranscriptPlayer
              ref={videoRef}
              mediaUrl={transcript.mediaUrl}
              currentTime={currentTime}
              isPlaying={isPlaying}
              playbackRate={playbackRate}
              onTimeUpdate={setCurrentTime}
              onPlaybackRateChange={setPlaybackRate}
              onPlayPause={setIsPlaying}
            />
          ) : (
            <div className="flex items-center justify-center h-64 bg-muted rounded-lg">
              <p className="text-muted-foreground">No media file available</p>
            </div>
          )}

          {/* Timeline */}
          <div className="mt-4">
            <TranscriptTimeline
              segments={transcript.segments}
              currentTime={currentTime}
              onSegmentClick={seekToSegment}
              selectedSegment={selectedSegment}
            />
          </div>
        </div>

        {/* Right Panel - Transcript */}
        <div className="w-full lg:w-2/5 border-l bg-muted/30 overflow-y-auto">
          <div className="p-4">
            <TranscriptControls
              isPlaying={isPlaying}
              playbackRate={playbackRate}
              onPlayPause={setIsPlaying}
              onPlaybackRateChange={setPlaybackRate}
              onSeek={(time) => {
                if (videoRef.current) {
                  videoRef.current.currentTime = time
                }
              }}
            />

            <div className="mt-4 space-y-2" ref={transcriptRef}>
              {filteredSegments.map((segment, index) => (
                <motion.div
                  key={segment.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedSegment === segment.id
                      ? 'bg-primary/10 border border-primary/20'
                      : 'bg-card hover:bg-card/80'
                  } ${
                    currentTime >= segment.startMs / 1000 &&
                    currentTime <= segment.endMs / 1000
                      ? 'ring-2 ring-primary/30'
                      : ''
                  }`}
                  onClick={() => {
                    setSelectedSegment(segment.id)
                    seekToSegment(segment.startMs)
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-primary bg-primary/10 px-2 py-1 rounded">
                          {segment.speaker}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatTime(segment.startMs)} - {formatTime(segment.endMs)}
                        </span>
                        {segment.confidence && (
                          <span className={`text-xs px-2 py-1 rounded ${
                            segment.confidence > 0.9
                              ? 'bg-green-100 text-green-800'
                              : segment.confidence > 0.7
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                          }`}>
                            {Math.round(segment.confidence * 100)}%
                          </span>
                        )}
                      </div>

                      {editMode ? (
                        <textarea
                          value={segment.text}
                          onChange={(e) => updateSegmentText(segment.id, e.target.value)}
                          className="w-full p-2 text-sm border rounded bg-background text-foreground resize-none"
                          rows={Math.max(2, segment.text.split('\n').length)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <p className="text-sm text-foreground leading-relaxed">
                          {segment.text}
                        </p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showExportDialog && (
        <ExportDialog
          transcript={transcript}
          onClose={() => setShowExportDialog(false)}
          onExport={onExport}
        />
      )}

      {showSpeakerMapping && (
        <SpeakerMapping
          transcript={transcript}
          onClose={() => setShowSpeakerMapping(false)}
          onUpdate={updateSpeakerLabel}
        />
      )}

      {showDictionary && (
        <DictionaryEditor
          onClose={() => setShowDictionary(false)}
        />
      )}
    </div>
  )
}

function formatTime(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}:${String(minutes % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
}
