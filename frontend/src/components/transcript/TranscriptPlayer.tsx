"use client"

import React, { forwardRef, useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Play, Pause, Volume2, VolumeX, SkipBack, SkipForward, RotateCcw } from 'lucide-react'

interface TranscriptPlayerProps {
  mediaUrl: string
  currentTime: number
  isPlaying: boolean
  playbackRate: number
  onTimeUpdate: (time: number) => void
  onPlaybackRateChange: (rate: number) => void
  onPlayPause: (playing: boolean) => void
}

export const TranscriptPlayer = forwardRef<HTMLVideoElement, TranscriptPlayerProps>(
  ({
    mediaUrl,
    currentTime,
    isPlaying,
    playbackRate,
    onTimeUpdate,
    onPlaybackRateChange,
    onPlayPause
  }, ref) => {
    const [volume, setVolume] = useState(1)
    const [isMuted, setIsMuted] = useState(false)
    const [duration, setDuration] = useState(0)
    const [showControls, setShowControls] = useState(true)
    const [isFullscreen, setIsFullscreen] = useState(false)

    const videoRef = useRef<HTMLVideoElement>(null)
    const controlsTimeoutRef = useRef<NodeJS.Timeout>()
    const containerRef = useRef<HTMLDivElement>(null)

    // Use a callback ref to avoid ref assignment issues
    const setVideoRef = (node: HTMLVideoElement | null) => {
      if (ref) {
        if (typeof ref === 'function') {
          ref(node)
        } else if (ref.current !== undefined) {
          ref.current = node
        }
      }
      // Store the node reference for internal use
      if (node) {
        // Access the ref through a different approach
        const videoElement = node as HTMLVideoElement
        if (videoElement && videoRef.current !== videoElement) {
          // Use Object.defineProperty to bypass readonly restriction
          Object.defineProperty(videoRef, 'current', {
            value: videoElement,
            writable: true,
            configurable: true
          })
        }
      }
    }

    useEffect(() => {
      const video = videoRef.current
      if (!video) return

      const handleLoadedMetadata = () => {
        setDuration(video.duration)
      }

      const handleTimeUpdate = () => {
        onTimeUpdate(video.currentTime)
      }

      const handleEnded = () => {
        onPlayPause(false)
      }

      video.addEventListener('loadedmetadata', handleLoadedMetadata)
      video.addEventListener('timeupdate', handleTimeUpdate)
      video.addEventListener('ended', handleEnded)

      return () => {
        video.removeEventListener('loadedmetadata', handleLoadedMetadata)
        video.removeEventListener('timeupdate', handleTimeUpdate)
        video.removeEventListener('ended', handleEnded)
      }
    }, [onTimeUpdate, onPlayPause])

    // Auto-hide controls
    useEffect(() => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current)
      }

      if (showControls) {
        controlsTimeoutRef.current = setTimeout(() => {
          setShowControls(false)
        }, 3000)
      }

      return () => {
        if (controlsTimeoutRef.current) {
          clearTimeout(controlsTimeoutRef.current)
        }
      }
    }, [showControls])

    const togglePlayPause = () => {
      const video = videoRef.current
      if (!video) return

      if (isPlaying) {
        video.pause()
        onPlayPause(false)
      } else {
        video.play()
        onPlayPause(true)
      }
    }

    const handleVolumeChange = (newVolume: number) => {
      const video = videoRef.current
      if (!video) return

      setVolume(newVolume)
      video.volume = newVolume
      setIsMuted(newVolume === 0)
    }

    const toggleMute = () => {
      const video = videoRef.current
      if (!video) return

      if (isMuted) {
        video.volume = volume
        setIsMuted(false)
      } else {
        video.volume = 0
        setIsMuted(true)
      }
    }

    const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
      const video = videoRef.current
      if (!video) return

      const rect = e.currentTarget.getBoundingClientRect()
      const clickX = e.clientX - rect.left
      const percentage = clickX / rect.width
      const newTime = percentage * duration

      video.currentTime = newTime
      onTimeUpdate(newTime)
    }

    const skipTime = (seconds: number) => {
      const video = videoRef.current
      if (!video) return

      const newTime = Math.max(0, Math.min(duration, video.currentTime + seconds))
      video.currentTime = newTime
      onTimeUpdate(newTime)
    }

    const handlePlaybackRateChange = (rate: number) => {
      const video = videoRef.current
      if (!video) return

      video.playbackRate = rate
      onPlaybackRateChange(rate)
    }

    const toggleFullscreen = () => {
      if (!document.fullscreenElement) {
        containerRef.current?.requestFullscreen()
        setIsFullscreen(true)
      } else {
        document.exitFullscreen()
        setIsFullscreen(false)
      }
    }

    const formatTime = (time: number) => {
      const minutes = Math.floor(time / 60)
      const seconds = Math.floor(time % 60)
      return `${minutes}:${String(seconds).padStart(2, '0')}`
    }

    return (
      <div
        ref={containerRef}
        className="relative bg-black rounded-lg overflow-hidden group"
        onMouseMove={() => setShowControls(true)}
        onMouseLeave={() => setShowControls(false)}
      >
        {/* Video Element */}
        <video
          ref={setVideoRef}
          src={mediaUrl}
          className="w-full h-auto max-h-[70vh] object-contain"
          playsInline
          preload="metadata"
        />

        {/* Overlay Controls */}
        <motion.div
          className={`absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent ${
            showControls ? 'opacity-100' : 'opacity-0'
          } transition-opacity duration-300`}
          initial={false}
          animate={{ opacity: showControls ? 1 : 0 }}
        >
          {/* Center Play/Pause Button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <button
              onClick={togglePlayPause}
              className="p-4 bg-black/50 rounded-full text-white hover:bg-black/70 transition-colors"
            >
              {isPlaying ? (
                <Pause className="w-8 h-8" />
              ) : (
                <Play className="w-8 h-8 ml-1" />
              )}
            </button>
          </div>

          {/* Bottom Controls */}
          <div className="absolute bottom-0 left-0 right-0 p-4">
            {/* Progress Bar */}
            <div className="mb-4">
              <div
                className="w-full h-2 bg-white/30 rounded-full cursor-pointer relative"
                onClick={handleSeek}
              >
                <div
                  className="h-full bg-primary rounded-full transition-all duration-100"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
                <div
                  className="absolute top-1/2 w-4 h-4 bg-primary rounded-full -translate-y-1/2 -translate-x-2"
                  style={{ left: `${(currentTime / duration) * 100}%` }}
                />
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => skipTime(-10)}
                  className="p-2 text-white hover:bg-white/20 rounded transition-colors"
                >
                  <SkipBack className="w-5 h-5" />
                </button>

                <button
                  onClick={togglePlayPause}
                  className="p-2 text-white hover:bg-white/20 rounded transition-colors"
                >
                  {isPlaying ? (
                    <Pause className="w-6 h-6" />
                  ) : (
                    <Play className="w-6 h-6 ml-0.5" />
                  )}
                </button>

                <button
                  onClick={() => skipTime(10)}
                  className="p-2 text-white hover:bg-white/20 rounded transition-colors"
                >
                  <SkipForward className="w-5 h-5" />
                </button>

                <button
                  onClick={() => skipTime(-30)}
                  className="p-2 text-white hover:bg-white/20 rounded transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-center space-x-4">
                {/* Playback Rate */}
                <select
                  value={playbackRate}
                  onChange={(e) => handlePlaybackRateChange(Number(e.target.value))}
                  className="bg-black/50 text-white text-sm rounded px-2 py-1 border-none focus:ring-2 focus:ring-primary"
                >
                  <option value={0.5}>0.5x</option>
                  <option value={0.75}>0.75x</option>
                  <option value={1}>1x</option>
                  <option value={1.25}>1.25x</option>
                  <option value={1.5}>1.5x</option>
                  <option value={2}>2x</option>
                </select>

                {/* Volume Control */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={toggleMute}
                    className="p-2 text-white hover:bg-white/20 rounded transition-colors"
                  >
                    {isMuted ? (
                      <VolumeX className="w-5 h-5" />
                    ) : (
                      <Volume2 className="w-5 h-5" />
                    )}
                  </button>

                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={isMuted ? 0 : volume}
                    onChange={(e) => handleVolumeChange(Number(e.target.value))}
                    className="w-20 h-2 bg-white/30 rounded-full appearance-none cursor-pointer slider"
                  />
                </div>

                {/* Time Display */}
                <div className="text-white text-sm font-mono">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Keyboard Shortcuts Info */}
        <div className="absolute top-4 right-4 text-white/70 text-xs bg-black/50 px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
          Space: Play/Pause • ←/→: Skip 10s • ↑/↓: Volume
        </div>
      </div>
    )
  }
)

TranscriptPlayer.displayName = 'TranscriptPlayer'
