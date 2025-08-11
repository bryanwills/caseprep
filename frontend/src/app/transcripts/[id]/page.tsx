"use client"

import React, { useState } from 'react'
import { TranscriptEditor } from '@/components/transcript/TranscriptEditor'
import { Transcript } from '@/types'

// Sample transcript data for development
const sampleTranscript: Transcript = {
  id: '1',
  matterId: 'matter-1',
  title: 'Court Hearing - Smith vs. Johnson',
  language: 'en',
  asrModel: 'faster-whisper-large-v3',
  diarizationModel: 'pyannote-2.1',
  totalDurationMs: 1265323, // ~21 minutes
  version: 1,
  encrypted: false,
  segments: [
    {
      id: 'seg-1',
      transcriptId: '1',
      speaker: 'Female 1',
      startMs: 30000,
      endMs: 55000,
      text: "All right, there are two cases on today's docket. First, we have Smith versus Johnson, case number 2024-CV-001234. This is a personal injury case. Mr. Smith, you may proceed with your opening statement.",
      confidence: 0.92,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-2',
      transcriptId: '1',
      speaker: 'Male 1',
      startMs: 55000,
      endMs: 85000,
      text: "Thank you, Your Honor. Ladies and gentlemen of the jury, on the morning of March 15th, 2023, my client, Sarah Smith, was driving to work when she was struck by a vehicle driven by the defendant, Mr. Johnson. The impact was severe and caused significant injuries to my client.",
      confidence: 0.89,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-3',
      transcriptId: '1',
      speaker: 'Female 1',
      startMs: 85000,
      endMs: 95000,
      text: "Mr. Johnson's attorney, do you have any objections to this opening statement?",
      confidence: 0.94,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-4',
      transcriptId: '1',
      speaker: 'Male 2',
      startMs: 95000,
      endMs: 105000,
      text: "No objections, Your Honor. The defense is ready to proceed.",
      confidence: 0.91,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-5',
      transcriptId: '1',
      speaker: 'Male 1',
      startMs: 105000,
      endMs: 135000,
      text: "The evidence will show that Mr. Johnson was driving at an excessive speed, failed to stop at a red light, and was distracted by his cell phone at the time of the accident. We will present testimony from eyewitnesses, accident reconstruction experts, and medical professionals.",
      confidence: 0.87,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-6',
      transcriptId: '1',
      speaker: 'Female 1',
      startMs: 135000,
      endMs: 145000,
      text: "Thank you, Mr. Smith. The jury will now hear the evidence in this case.",
      confidence: 0.93,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-7',
      transcriptId: '1',
      speaker: 'Female 2',
      startMs: 145000,
      endMs: 175000,
      text: "Your Honor, the plaintiff calls Dr. Emily Rodriguez to the stand. Dr. Rodriguez is a board-certified orthopedic surgeon who treated Ms. Smith following the accident.",
      confidence: 0.88,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-8',
      transcriptId: '1',
      speaker: 'Female 1',
      startMs: 175000,
      endMs: 185000,
      text: "Dr. Rodriguez, please come forward and be sworn in.",
      confidence: 0.95,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-9',
      transcriptId: '1',
      speaker: 'Female 3',
      startMs: 185000,
      endMs: 215000,
      text: "I do solemnly swear that the testimony I am about to give shall be the truth, the whole truth, and nothing but the truth, so help me God.",
      confidence: 0.90,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: 'seg-10',
      transcriptId: '1',
      speaker: 'Female 1',
      startMs: 215000,
      endMs: 225000,
      text: "Please be seated. You may proceed with your direct examination.",
      confidence: 0.94,
      createdAt: '2024-01-15T10:00:00Z'
    }
  ],
  speakerMap: {
    'Female 1': 'Judge Sarah Williams',
    'Male 1': 'Attorney Robert Smith',
    'Male 2': 'Attorney Michael Johnson',
    'Female 2': 'Attorney Lisa Chen',
    'Female 3': 'Dr. Emily Rodriguez'
  },
  mediaUrl: '/sample-court-hearing.mp4', // This would be a real video file in production
  createdAt: '2024-01-15T10:00:00Z',
  updatedAt: '2024-01-15T10:00:00Z'
}

export default function TranscriptPage() {
  const [transcript, setTranscript] = useState<Transcript>(sampleTranscript)

  const handleTranscriptUpdate = (updatedTranscript: Transcript) => {
    setTranscript(updatedTranscript)
    // In production, this would save to the backend
    console.log('Transcript updated:', updatedTranscript)
  }

  const handleExport = (format: string) => {
    // In production, this would trigger the export process
    console.log('Exporting transcript in format:', format)
    alert(`Exporting transcript in ${format.toUpperCase()} format...`)
  }

  return (
    <div className="min-h-screen bg-background">
      <TranscriptEditor
        transcript={transcript}
        onTranscriptUpdate={handleTranscriptUpdate}
        onExport={handleExport}
      />
    </div>
  )
}
