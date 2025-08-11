"use client"

import React from 'react'
import { Play, Pause, SkipBack, SkipForward, RotateCcw, Search, Filter } from 'lucide-react'

interface TranscriptControlsProps {
  isPlaying: boolean
  playbackRate: number
  onPlayPause: (playing: boolean) => void
  onPlaybackRateChange: (rate: number) => void
  onSeek: (time: number) => void
}

export function TranscriptControls({
  isPlaying,
  playbackRate,
  onPlayPause,
  onPlaybackRateChange,
  onSeek
}: TranscriptControlsProps) {
  const skipTime = (seconds: number) => {
    // This will be handled by the parent component
    // We just need to calculate the new time
    const currentTime = 0 // This should come from parent
    const newTime = Math.max(0, currentTime + seconds)
    onSeek(newTime)
  }

  return (
    <div className="flex items-center justify-between p-3 bg-card rounded-lg border">
      {/* Playback Controls */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => skipTime(-30)}
          className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
          title="Skip back 30 seconds"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        <button
          onClick={() => skipTime(-10)}
          className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
          title="Skip back 10 seconds"
        >
          <SkipBack className="w-5 h-5" />
        </button>

        <button
          onClick={() => onPlayPause(!isPlaying)}
          className="p-3 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 transition-colors"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <Pause className="w-5 h-5" />
          ) : (
            <Play className="w-5 h-5 ml-0.5" />
          )}
        </button>

        <button
          onClick={() => skipTime(10)}
          className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
          title="Skip forward 10 seconds"
        >
          <SkipForward className="w-5 h-5" />
        </button>
      </div>

      {/* Playback Rate */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-muted-foreground">Speed:</span>
        <select
          value={playbackRate}
          onChange={(e) => onPlaybackRateChange(Number(e.target.value))}
          className="bg-background text-foreground text-sm rounded px-2 py-1 border focus:ring-2 focus:ring-primary focus:border-transparent"
        >
          <option value={0.5}>0.5x</option>
          <option value={0.75}>0.75x</option>
          <option value={1}>1x</option>
          <option value={1.25}>1.25x</option>
          <option value={1.5}>1.5x</option>
          <option value={2}>2x</option>
        </select>
      </div>

      {/* Additional Controls */}
      <div className="flex items-center space-x-2">
        <button
          className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
          title="Search transcript"
        >
          <Search className="w-4 h-4" />
        </button>

        <button
          className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
          title="Filter segments"
        >
          <Filter className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
