"use client"

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, User, Edit2, Save, XCircle } from 'lucide-react'
import { Transcript } from '@/types'

interface SpeakerMappingProps {
  transcript: Transcript
  onClose: () => void
  onUpdate: (oldLabel: string, newLabel: string) => void
}

interface SpeakerEntry {
  placeholder: string
  alias: string
  isEditing: boolean
  editValue: string
}

export function SpeakerMapping({ transcript, onClose, onUpdate }: SpeakerMappingProps) {
  const [speakers, setSpeakers] = useState<SpeakerEntry[]>([])
  const [newSpeaker, setNewSpeaker] = useState('')

  // Initialize speakers from transcript
  useEffect(() => {
    const uniqueSpeakers = Array.from(new Set(transcript.segments.map(s => s.speaker)))
    const speakerEntries: SpeakerEntry[] = uniqueSpeakers.map(speaker => ({
      placeholder: speaker,
      alias: transcript.speakerMap?.[speaker] || '',
      isEditing: false,
      editValue: transcript.speakerMap?.[speaker] || ''
    }))
    setSpeakers(speakerEntries)
  }, [transcript])

  const handleEdit = (index: number) => {
    setSpeakers(prev => prev.map((s, i) =>
      i === index ? { ...s, isEditing: true } : s
    ))
  }

  const handleSave = (index: number) => {
    const speaker = speakers[index]
    if (speaker && speaker.editValue.trim()) {
      onUpdate(speaker.placeholder, speaker.editValue.trim())
      setSpeakers(prev => prev.map((s, i) =>
        i === index ? { ...s, alias: speaker.editValue.trim(), isEditing: false } : s
      ))
    }
  }

  const handleCancel = (index: number) => {
    setSpeakers(prev => prev.map((s, i) =>
      i === index ? { ...s, isEditing: false, editValue: s.alias } : s
    ))
  }

  const handleRemove = (index: number) => {
    const speaker = speakers[index]
    if (speaker && speaker.alias) {
      onUpdate(speaker.placeholder, '')
      setSpeakers(prev => prev.map((s, i) =>
        i === index ? { ...s, alias: '', editValue: '' } : s
      ))
    }
  }

  const addNewSpeaker = () => {
    if (newSpeaker.trim() && !speakers.some(s => s.placeholder === newSpeaker.trim())) {
      const newEntry: SpeakerEntry = {
        placeholder: newSpeaker.trim(),
        alias: '',
        isEditing: false,
        editValue: ''
      }
      setSpeakers(prev => [...prev, newEntry])
      setNewSpeaker('')
    }
  }

  const getSpeakerColor = (index: number) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-orange-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-teal-500',
      'bg-red-500'
    ]
    return colors[index % colors.length]
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-background rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div>
              <h2 className="text-xl font-semibold text-foreground">Speaker Mapping</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Map speaker placeholders to actual names
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Add New Speaker */}
            <div>
              <h3 className="text-sm font-medium text-foreground mb-3">Add Speaker Placeholder</h3>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newSpeaker}
                  onChange={(e) => setNewSpeaker(e.target.value)}
                  placeholder="Enter speaker placeholder (e.g., 'Female 1')"
                  className="flex-1 px-3 py-2 border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && addNewSpeaker()}
                />
                <button
                  onClick={addNewSpeaker}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  Add
                </button>
              </div>
            </div>

            {/* Speaker List */}
            <div>
              <h3 className="text-sm font-medium text-foreground mb-3">Speaker Mappings</h3>
              <div className="space-y-3">
                {speakers.map((speaker, index) => (
                  <motion.div
                    key={speaker.placeholder}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center space-x-3 p-3 bg-muted rounded-lg"
                  >
                    {/* Speaker Icon */}
                    <div className={`w-8 h-8 rounded-full ${getSpeakerColor(index)} flex items-center justify-center text-white text-sm font-medium`}>
                      <User className="w-4 h-4" />
                    </div>

                    {/* Speaker Info */}
                    <div className="flex-1">
                      <div className="text-sm font-medium text-foreground">
                        {speaker.placeholder}
                      </div>
                      {speaker.alias && (
                        <div className="text-xs text-muted-foreground">
                          Mapped to: {speaker.alias}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      {speaker.isEditing ? (
                        <>
                          <input
                            type="text"
                            value={speaker.editValue}
                            onChange={(e) => setSpeakers(prev => prev.map((s, i) =>
                              i === index ? { ...s, editValue: e.target.value } : s
                            ))}
                            placeholder="Enter actual name"
                            className="px-3 py-1 text-sm border rounded bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                            autoFocus
                          />
                          <button
                            onClick={() => handleSave(index)}
                            className="p-1 text-green-600 hover:bg-green-100 rounded transition-colors"
                            title="Save"
                          >
                            <Save className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleCancel(index)}
                            className="p-1 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                            title="Cancel"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => handleEdit(index)}
                            className="p-1 text-blue-600 hover:bg-blue-100 rounded transition-colors"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          {speaker.alias && (
                            <button
                              onClick={() => handleRemove(index)}
                              className="p-1 text-red-600 hover:bg-red-100 rounded transition-colors"
                              title="Remove mapping"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </motion.div>
                ))}

                {speakers.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No speakers detected in transcript
                  </div>
                )}
              </div>
            </div>

            {/* Usage Info */}
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="text-sm font-medium text-blue-900 mb-2">How it works</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Speaker placeholders are automatically detected from the transcript</li>
                <li>• Map each placeholder to the actual person's name</li>
                <li>• Changes are applied immediately to the transcript</li>
                <li>• Mappings are saved with your transcript</li>
              </ul>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end p-6 border-t bg-muted/30">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              Done
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
