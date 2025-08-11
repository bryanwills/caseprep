/**
 * Theme management hook with persistence and system theme detection
 */

'use client'

import { useEffect, useState } from 'react'
import { 
  Theme, 
  getStoredTheme, 
  setStoredTheme, 
  applyTheme, 
  getEffectiveTheme,
  watchSystemTheme 
} from '@/lib/theme'

interface UseThemeReturn {
  theme: Theme
  effectiveTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  themes: { value: Theme; label: string; description: string }[]
}

export function useTheme(): UseThemeReturn {
  const [theme, setThemeState] = useState<Theme>('system')
  const [effectiveTheme, setEffectiveTheme] = useState<'light' | 'dark'>('light')

  // Initialize theme on mount
  useEffect(() => {
    const storedTheme = getStoredTheme()
    const effective = getEffectiveTheme(storedTheme)
    
    setThemeState(storedTheme)
    setEffectiveTheme(effective)
    applyTheme(storedTheme)
  }, [])

  // Watch for system theme changes when using 'system'
  useEffect(() => {
    if (theme !== 'system') return

    const cleanup = watchSystemTheme((systemTheme) => {
      setEffectiveTheme(systemTheme)
      applyTheme('system')
    })

    return cleanup
  }, [theme])

  const setTheme = (newTheme: Theme) => {
    const effective = getEffectiveTheme(newTheme)
    
    setThemeState(newTheme)
    setEffectiveTheme(effective)
    setStoredTheme(newTheme)
    applyTheme(newTheme)
  }

  const toggleTheme = () => {
    const themeOrder: Theme[] = ['system', 'light', 'dark']
    const currentIndex = themeOrder.indexOf(theme)
    const nextIndex = (currentIndex + 1) % themeOrder.length
    setTheme(themeOrder[nextIndex])
  }

  const themes = [
    {
      value: 'system' as Theme,
      label: 'System',
      description: 'Use system preference'
    },
    {
      value: 'light' as Theme,
      label: 'Light',
      description: 'Light theme'
    },
    {
      value: 'dark' as Theme,
      label: 'Dark',
      description: 'Dark theme'
    }
  ]

  return {
    theme,
    effectiveTheme,
    setTheme,
    toggleTheme,
    themes
  }
}