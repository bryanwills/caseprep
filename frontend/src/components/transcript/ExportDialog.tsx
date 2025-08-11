"use client"

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Download, FileText, FileVideo, FileAudio, Settings } from 'lucide-react'
import { Transcript } from '@/types'

interface ExportDialogProps {
  transcript: Transcript
  onClose: () => void
  onExport: (format: string) => void
}

interface ExportFormat {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  extensions: string[]
}

const exportFormats: ExportFormat[] = [
  {
    id: 'srt',
    name: 'SRT (SubRip)',
    description: 'Standard subtitle format for video players',
    icon: <FileText className="w-5 h-5" />,
    extensions: ['.srt']
  },
  {
    id: 'vtt',
    name: 'WebVTT',
    description: 'Web video text tracks format',
    icon: <FileText className="w-5 h-5" />,
    extensions: ['.vtt']
  },
  {
    id: 'docx',
    name: 'Microsoft Word',
    description: 'Editable document with formatting',
    icon: <FileText className="w-5 h-5" />,
    extensions: ['.docx']
  },
  {
    id: 'pdf',
    name: 'PDF Document',
    description: 'Professional quote pack format',
    icon: <FileText className="w-5 h-5" />,
    extensions: ['.pdf']
  },
  {
    id: 'csv',
    name: 'CSV Spreadsheet',
    description: 'Data analysis and processing',
    icon: <FileText className="w-5 h-5" />,
    extensions: ['.csv']
  },
  {
    id: 'json',
    name: 'JSON Data',
    description: 'Structured data with timestamps',
    icon: <FileText className="w-5 h-5" />,
    extensions: ['.json']
  }
]

export function ExportDialog({ transcript, onClose, onExport }: ExportDialogProps) {
  const [selectedFormat, setSelectedFormat] = useState<string>('srt')
  const [includeMetadata, setIncludeMetadata] = useState(true)
  const [includeConfidence, setIncludeConfidence] = useState(true)
  const [includeSpeakerMapping, setIncludeSpeakerMapping] = useState(true)
  const [exporting, setExporting] = useState(false)

  const handleExport = async () => {
    setExporting(true)

    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Call the export function
      onExport(selectedFormat)
      onClose()
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setExporting(false)
    }
  }

  const selectedFormatData = exportFormats.find(f => f.id === selectedFormat)

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
              <h2 className="text-xl font-semibold text-foreground">Export Transcript</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Export "{transcript.title || 'Untitled'}" in your preferred format
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
            {/* Format Selection */}
            <div>
              <h3 className="text-sm font-medium text-foreground mb-3">Export Format</h3>
              <div className="grid grid-cols-2 gap-3">
                {exportFormats.map((format) => (
                  <button
                    key={format.id}
                    onClick={() => setSelectedFormat(format.id)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      selectedFormat === format.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="text-primary">{format.icon}</div>
                      <div className="text-left">
                        <div className="font-medium text-foreground">{format.name}</div>
                        <div className="text-xs text-muted-foreground">{format.description}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Export Options */}
            <div>
              <h3 className="text-sm font-medium text-foreground mb-3">Export Options</h3>
              <div className="space-y-3">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={includeMetadata}
                    onChange={(e) => setIncludeMetadata(e.target.checked)}
                    className="rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <span className="text-sm text-foreground">Include metadata (duration, language, models used)</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={includeConfidence}
                    onChange={(e) => setIncludeConfidence(e.target.checked)}
                    className="rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <span className="text-sm text-foreground">Include confidence scores</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={includeSpeakerMapping}
                    onChange={(e) => setIncludeSpeakerMapping(e.target.checked)}
                    className="rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <span className="text-sm text-foreground">Include speaker mapping</span>
                </label>
              </div>
            </div>

            {/* Preview */}
            {selectedFormatData && (
              <div>
                <h3 className="text-sm font-medium text-foreground mb-3">Preview</h3>
                <div className="p-4 bg-muted rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    {selectedFormatData.icon}
                    <span className="font-medium text-foreground">{selectedFormatData.name}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    File will be exported as: <code className="bg-background px-2 py-1 rounded text-xs">
                      {transcript.title || 'transcript'}{selectedFormatData.extensions[0]}
                    </code>
                  </p>
                  {selectedFormat === 'pdf' && (
                    <p className="text-sm text-muted-foreground mt-2">
                      PDF will include professional formatting suitable for legal documents and quote packs.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t bg-muted/30">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={exporting}
              className="flex items-center space-x-2 px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {exporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                  <span>Exporting...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Export {selectedFormatData?.name}</span>
                </>
              )}
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
