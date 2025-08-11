"use client"

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Plus, Edit2, Trash2, Save, XCircle, BookOpen } from 'lucide-react'

interface DictionaryEditorProps {
  onClose: () => void
}

interface DictionaryRule {
  id: string
  pattern: string
  replacement: string
  scope: 'word' | 'phrase' | 'regex'
  isActive: boolean
  isEditing: boolean
  editPattern: string
  editReplacement: string
  editScope: 'word' | 'phrase' | 'regex'
}

export function DictionaryEditor({ onClose }: DictionaryEditorProps) {
  const [rules, setRules] = useState<DictionaryRule[]>([
    {
      id: '1',
      pattern: 'attorney general',
      replacement: 'Attorney General',
      scope: 'phrase',
      isActive: true,
      isEditing: false,
      editPattern: 'attorney general',
      editReplacement: 'Attorney General',
      editScope: 'phrase'
    },
    {
      id: '2',
      pattern: 'district court',
      replacement: 'District Court',
      scope: 'phrase',
      isActive: true,
      isEditing: false,
      editPattern: 'district court',
      editReplacement: 'District Court',
      editScope: 'phrase'
    }
  ])

  const [newRule, setNewRule] = useState({
    pattern: '',
    replacement: '',
    scope: 'word' as const
  })
  const [showAddForm, setShowAddForm] = useState(false)

  const addRule = () => {
    if (newRule.pattern.trim() && newRule.replacement.trim()) {
      const rule: DictionaryRule = {
        id: Date.now().toString(),
        pattern: newRule.pattern.trim(),
        replacement: newRule.replacement.trim(),
        scope: newRule.scope,
        isActive: true,
        isEditing: false,
        editPattern: newRule.pattern.trim(),
        editReplacement: newRule.replacement.trim(),
        editScope: newRule.scope
      }

      setRules(prev => [...prev, rule])
      setNewRule({ pattern: '', replacement: '', scope: 'word' })
      setShowAddForm(false)
    }
  }

  const startEdit = (id: string) => {
    setRules(prev => prev.map(rule =>
      rule.id === id
        ? { ...rule, isEditing: true }
        : rule
    ))
  }

  const saveEdit = (id: string) => {
    setRules(prev => prev.map(rule => {
      if (rule.id === id) {
        return {
          ...rule,
          pattern: rule.editPattern,
          replacement: rule.editReplacement,
          scope: rule.editScope,
          isEditing: false
        }
      }
      return rule
    }))
  }

  const cancelEdit = (id: string) => {
    setRules(prev => prev.map(rule => {
      if (rule.id === id) {
        return {
          ...rule,
          editPattern: rule.pattern,
          editReplacement: rule.replacement,
          editScope: rule.scope,
          isEditing: false
        }
      }
      return rule
    }))
  }

  const deleteRule = (id: string) => {
    setRules(prev => prev.filter(rule => rule.id !== id))
  }

  const toggleRule = (id: string) => {
    setRules(prev => prev.map(rule =>
      rule.id === id ? { ...rule, isActive: !rule.isActive } : rule
    ))
  }

  const getScopeDescription = (scope: string) => {
    switch (scope) {
      case 'word':
        return 'Exact word match'
      case 'phrase':
        return 'Exact phrase match'
      case 'regex':
        return 'Regular expression'
      default:
        return ''
    }
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
          className="bg-background rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div className="flex items-center space-x-3">
              <BookOpen className="w-6 h-6 text-primary" />
              <div>
                <h2 className="text-xl font-semibold text-foreground">Dictionary Editor</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Create custom correction rules for your transcripts
                </p>
              </div>
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
            {/* Add New Rule */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-foreground">Add New Rule</h3>
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="flex items-center space-x-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  <span>{showAddForm ? 'Cancel' : 'Add Rule'}</span>
                </button>
              </div>

              <AnimatePresence>
                {showAddForm && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="p-4 bg-muted rounded-lg space-y-4"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Pattern
                        </label>
                        <input
                          type="text"
                          value={newRule.pattern}
                          onChange={(e) => setNewRule(prev => ({ ...prev, pattern: e.target.value }))}
                          placeholder="Text to find"
                          className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Replacement
                        </label>
                        <input
                          type="text"
                          value={newRule.replacement}
                          onChange={(e) => setNewRule(prev => ({ ...prev, replacement: e.target.value }))}
                          placeholder="Text to replace with"
                          className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Scope
                        </label>
                        <select
                          value={newRule.scope}
                          onChange={(e) => setNewRule(prev => ({ ...prev, scope: e.target.value as any }))}
                          className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                        >
                          <option value="word">Word</option>
                          <option value="phrase">Phrase</option>
                          <option value="regex">Regex</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => setShowAddForm(false)}
                        className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={addRule}
                        disabled={!newRule.pattern.trim() || !newRule.replacement.trim()}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Add Rule
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Rules List */}
            <div>
              <h3 className="text-sm font-medium text-foreground mb-3">
                Dictionary Rules ({rules.filter(r => r.isActive).length} active)
              </h3>

              <div className="space-y-3">
                {rules.map((rule, index) => (
                  <motion.div
                    key={rule.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`p-4 rounded-lg border transition-all ${
                      rule.isActive ? 'bg-card border-border' : 'bg-muted/50 border-muted'
                    }`}
                  >
                    {rule.isEditing ? (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <input
                            type="text"
                            value={rule.editPattern}
                            onChange={(e) => setRules(prev => prev.map(r =>
                              r.id === rule.id ? { ...r, editPattern: e.target.value } : r
                            ))}
                            className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                          />
                        </div>

                        <div>
                          <input
                            type="text"
                            value={rule.editReplacement}
                            onChange={(e) => setRules(prev => prev.map(r =>
                              r.id === rule.id ? { ...r, editReplacement: e.target.value } : r
                            ))}
                            className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                          />
                        </div>

                        <div className="flex items-center space-x-2">
                          <select
                            value={rule.editScope}
                            onChange={(e) => setRules(prev => prev.map(r =>
                              r.id === rule.id ? { ...r, editScope: e.target.value as any } : r
                            ))}
                            className="flex-1 px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                          >
                            <option value="word">Word</option>
                            <option value="phrase">Phrase</option>
                            <option value="regex">Regex</option>
                          </select>

                          <button
                            onClick={() => saveEdit(rule.id)}
                            className="p-2 text-green-600 hover:bg-green-100 rounded transition-colors"
                            title="Save"
                          >
                            <Save className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => cancelEdit(rule.id)}
                            className="p-2 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                            title="Cancel"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <div className="text-sm font-medium text-foreground">
                              {rule.pattern}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Pattern
                            </div>
                          </div>

                          <div>
                            <div className="text-sm font-medium text-foreground">
                              {rule.replacement}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Replacement
                            </div>
                          </div>

                          <div>
                            <div className="text-sm font-medium text-foreground">
                              {rule.scope}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {getScopeDescription(rule.scope)}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 ml-4">
                          <button
                            onClick={() => toggleRule(rule.id)}
                            className={`px-3 py-1 text-xs rounded-full transition-colors ${
                              rule.isActive
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {rule.isActive ? 'Active' : 'Inactive'}
                          </button>

                          <button
                            onClick={() => startEdit(rule.id)}
                            className="p-2 text-blue-600 hover:bg-blue-100 rounded transition-colors"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => deleteRule(rule.id)}
                            className="p-2 text-red-600 hover:bg-red-100 rounded transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}

                {rules.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No dictionary rules created yet
                  </div>
                )}
              </div>
            </div>

            {/* Usage Info */}
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="text-sm font-medium text-blue-900 mb-2">How dictionary rules work</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• <strong>Word:</strong> Exact word match (e.g., "attorney" → "Attorney")</li>
                <li>• <strong>Phrase:</strong> Exact phrase match (e.g., "district court" → "District Court")</li>
                <li>• <strong>Regex:</strong> Regular expression pattern for complex replacements</li>
                <li>• Rules are applied in order when processing transcripts</li>
                <li>• Active rules are automatically applied to new transcripts</li>
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
