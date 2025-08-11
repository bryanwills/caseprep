"use client"

import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import { TranscriptSegment } from '@/types'

interface TranscriptTimelineProps {
  segments: TranscriptSegment[]
  currentTime: number
  onSegmentClick: (startTime: number) => void
  selectedSegment: string | null
}

export function TranscriptTimeline({
  segments,
  currentTime,
  onSegmentClick,
  selectedSegment
}: TranscriptTimelineProps) {
  const totalDuration = useMemo(() => {
    if (segments.length === 0) return 0
    return Math.max(...segments.map(s => s.endMs))
  }, [segments])

  const currentSegment = useMemo(() => {
    return segments.find(segment =>
      currentTime >= segment.startMs / 1000 &&
      currentTime <= segment.endMs / 1000
    )
  }, [segments, currentTime])

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)

    if (hours > 0) {
      return `${hours}:${String(minutes % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
    }
    return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
  }

  const getSegmentColor = (segment: TranscriptSegment) => {
    if (segment.id === selectedSegment) {
      return 'bg-primary'
    }

    // Color by speaker (cycling through a palette)
    const speakerColors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-orange-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-teal-500',
      'bg-red-500'
    ]

    const speakerIndex = segments
      .map(s => s.speaker)
      .filter((s, i, arr) => arr.indexOf(s) === i)
      .indexOf(segment.speaker)

    return speakerColors[speakerIndex % speakerColors.length]
  }

  if (segments.length === 0) {
    return (
      <div className="w-full h-20 bg-muted rounded-lg flex items-center justify-center text-muted-foreground">
        No transcript segments available
      </div>
    )
  }

  return (
    <div className="w-full">
      {/* Timeline Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-foreground">Timeline</h3>
        <div className="text-xs text-muted-foreground">
          {formatTime(totalDuration)} total
        </div>
      </div>

      {/* Timeline Container */}
      <div className="relative w-full h-16 bg-muted rounded-lg overflow-hidden">
        {/* Time Markers */}
        <div className="absolute inset-0 flex items-end justify-between px-2 pb-1 text-xs text-muted-foreground">
          <span>0:00</span>
          <span>{formatTime(totalDuration)}</span>
        </div>

        {/* Current Time Indicator */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-primary z-10 transition-all duration-100"
          style={{
            left: `${(currentTime * 1000 / totalDuration) * 100}%`
          }}
        />

        {/* Segments */}
        <div className="relative w-full h-full">
          {segments.map((segment, index) => {
            const left = (segment.startMs / totalDuration) * 100
            const width = ((segment.endMs - segment.startMs) / totalDuration) * 100

            return (
              <motion.div
                key={segment.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.02 }}
                className={`absolute top-1 bottom-1 rounded cursor-pointer transition-all duration-200 hover:scale-y-110 ${
                  getSegmentColor(segment)
                } ${
                  segment.id === selectedSegment
                    ? 'ring-2 ring-primary ring-offset-2 ring-offset-background'
                    : ''
                } ${
                  currentTime >= segment.startMs / 1000 &&
                  currentTime <= segment.endMs / 1000
                    ? 'ring-2 ring-white ring-offset-1 ring-offset-background'
                    : ''
                }`}
                style={{
                  left: `${left}%`,
                  width: `${width}%`,
                  minWidth: '4px'
                }}
                onClick={() => onSegmentClick(segment.startMs)}
                title={`${segment.speaker}: ${segment.text.substring(0, 50)}${segment.text.length > 50 ? '...' : ''}`}
              />
            )
          })}
        </div>

        {/* Speaker Legend */}
        <div className="absolute top-0 right-0 p-2">
          <div className="flex flex-wrap gap-1 max-w-32">
            {Array.from(new Set(segments.map(s => s.speaker))).map((speaker, index) => {
              const speakerColors = [
                'bg-blue-500',
                'bg-green-500',
                'bg-purple-500',
                'bg-orange-500',
                'bg-pink-500',
                'bg-indigo-500',
                'bg-teal-500',
                'bg-red-500'
              ]

              return (
                <div key={speaker} className="flex items-center space-x-1">
                  <div className={`w-3 h-3 rounded-full ${speakerColors[index % speakerColors.length]}`} />
                  <span className="text-xs text-white font-medium truncate max-w-16">
                    {speaker}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Current Segment Info */}
      {currentSegment && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 p-3 bg-card rounded-lg border"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-primary">
                {currentSegment.speaker}
              </span>
              <span className="text-xs text-muted-foreground">
                {formatTime(currentSegment.startMs)} - {formatTime(currentSegment.endMs)}
              </span>
            </div>
            {currentSegment.confidence && (
              <span className={`text-xs px-2 py-1 rounded ${
                currentSegment.confidence > 0.9
                  ? 'bg-green-100 text-green-800'
                  : currentSegment.confidence > 0.7
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
              }`}>
                {Math.round(currentSegment.confidence * 100)}% confidence
              </span>
            )}
          </div>
          <p className="text-sm text-foreground mt-2 line-clamp-2">
            {currentSegment.text}
          </p>
        </motion.div>
      )}
    </div>
  )
}
