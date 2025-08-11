"use client"

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  User,
  Shield,
  Bell,
  Palette,
  Database,
  Download,
  Trash2,
  Save,
  X
} from 'lucide-react'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile')
  const [isEditing, setIsEditing] = useState(false)

  const tabs = [
    { id: 'profile', name: 'Profile', icon: <User className="w-4 h-4" /> },
    { id: 'security', name: 'Security', icon: <Shield className="w-4 h-4" /> },
    { id: 'notifications', name: 'Notifications', icon: <Bell className="w-4 h-4" /> },
    { id: 'appearance', name: 'Appearance', icon: <Palette className="w-4 h-4" /> },
    { id: 'data', name: 'Data & Privacy', icon: <Database className="w-4 h-4" /> },
  ]

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Manage your account preferences and settings
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  }`}
                >
                  {tab.icon}
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className="bg-card rounded-lg border p-6"
            >
              {activeTab === 'profile' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-6">Profile Settings</h2>

                  <div className="space-y-6">
                    {/* Profile Picture */}
                    <div className="flex items-center space-x-4">
                      <div className="w-20 h-20 bg-muted rounded-full flex items-center justify-center">
                        <User className="w-10 h-10 text-muted-foreground" />
                      </div>
                      <div>
                        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
                          Change Photo
                        </button>
                        <p className="text-sm text-muted-foreground mt-1">
                          JPG, PNG or GIF. Max size 2MB.
                        </p>
                      </div>
                    </div>

                    {/* Form Fields */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          First Name
                        </label>
                        <input
                          type="text"
                          defaultValue="John"
                          className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Last Name
                        </label>
                        <input
                          type="text"
                          defaultValue="Doe"
                          className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Email
                        </label>
                        <input
                          type="email"
                          defaultValue="john.doe@example.com"
                          className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Job Title
                        </label>
                        <input
                          type="text"
                          defaultValue="Senior Attorney"
                          className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex justify-end space-x-3 pt-4 border-t">
                      <button
                        onClick={() => setIsEditing(false)}
                        className="px-4 py-2 border rounded-md text-foreground hover:bg-muted transition-colors"
                      >
                        Cancel
                      </button>
                      <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center space-x-2">
                        <Save className="w-4 h-4" />
                        <span>Save Changes</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'security' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-6">Security Settings</h2>

                  <div className="space-y-6">
                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-foreground">Two-Factor Authentication</h3>
                          <p className="text-sm text-muted-foreground">
                            Add an extra layer of security to your account
                          </p>
                        </div>
                        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
                          Enable
                        </button>
                      </div>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-foreground">Change Password</h3>
                          <p className="text-sm text-muted-foreground">
                            Update your password regularly for security
                          </p>
                        </div>
                        <button className="px-4 py-2 border rounded-md text-foreground hover:bg-muted transition-colors">
                          Change
                        </button>
                      </div>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-foreground">Login History</h3>
                          <p className="text-sm text-muted-foreground">
                            View recent login activity
                          </p>
                        </div>
                        <button className="px-4 py-2 border rounded-md text-foreground hover:bg-muted transition-colors">
                          View
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'notifications' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-6">Notification Preferences</h2>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h3 className="font-medium text-foreground">Email Notifications</h3>
                        <p className="text-sm text-muted-foreground">
                          Receive notifications via email
                        </p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h3 className="font-medium text-foreground">Push Notifications</h3>
                        <p className="text-sm text-muted-foreground">
                          Receive push notifications in your browser
                        </p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h3 className="font-medium text-foreground">Transcription Complete</h3>
                        <p className="text-sm text-muted-foreground">
                          Notify when transcription jobs complete
                        </p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h3 className="font-medium text-foreground">System Updates</h3>
                        <p className="text-sm text-muted-foreground">
                          Notify about system maintenance and updates
                        </p>
                      </div>
                      <input type="checkbox" className="rounded" />
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'appearance' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-6">Appearance Settings</h2>

                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Theme
                      </label>
                      <select className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent">
                        <option value="system">System</option>
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Font Size
                      </label>
                      <select className="w-full px-3 py-2 border rounded-md bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent">
                        <option value="small">Small</option>
                        <option value="medium" selected>Medium</option>
                        <option value="large">Large</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Color Scheme
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        <button className="p-4 border-2 border-primary rounded-lg bg-primary text-primary-foreground">
                          Default
                        </button>
                        <button className="p-4 border rounded-lg bg-blue-500 text-white">
                          Blue
                        </button>
                        <button className="p-4 border rounded-lg bg-green-500 text-white">
                          Green
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'data' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-6">Data & Privacy</h2>

                  <div className="space-y-6">
                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-foreground">Export Data</h3>
                          <p className="text-sm text-muted-foreground">
                            Download a copy of your data
                          </p>
                        </div>
                        <button className="px-4 py-2 border rounded-md text-foreground hover:bg-muted transition-colors flex items-center space-x-2">
                          <Download className="w-4 h-4" />
                          <span>Export</span>
                        </button>
                      </div>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-foreground">Delete Account</h3>
                          <p className="text-sm text-muted-foreground">
                            Permanently delete your account and all data
                          </p>
                        </div>
                        <button className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center space-x-2">
                          <Trash2 className="w-4 h-4" />
                          <span>Delete</span>
                        </button>
                      </div>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-foreground">Data Retention</h3>
                          <p className="text-sm text-muted-foreground">
                            Manage how long your data is kept
                          </p>
                        </div>
                        <button className="px-4 py-2 border rounded-md text-foreground hover:bg-muted transition-colors">
                          Configure
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}
