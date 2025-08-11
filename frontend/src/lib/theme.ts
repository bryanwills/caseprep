/**
 * Theme management utilities with localStorage persistence
 */

export type Theme = 'light' | 'dark' | 'system'

const THEME_STORAGE_KEY = 'caseprep-theme'

/**
 * Get the current system theme preference
 */
export function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/**
 * Get the effective theme (resolves 'system' to actual theme)
 */
export function getEffectiveTheme(theme: Theme): 'light' | 'dark' {
  return theme === 'system' ? getSystemTheme() : theme
}

/**
 * Get the stored theme from localStorage
 */
export function getStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'system'
  
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY) as Theme
    return stored && ['light', 'dark', 'system'].includes(stored) ? stored : 'system'
  } catch {
    return 'system'
  }
}

/**
 * Store theme preference in localStorage
 */
export function setStoredTheme(theme: Theme): void {
  if (typeof window === 'undefined') return
  
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    // localStorage might be disabled
  }
}

/**
 * Apply theme to document
 */
export function applyTheme(theme: Theme): void {
  if (typeof window === 'undefined') return
  
  const effectiveTheme = getEffectiveTheme(theme)
  const root = document.documentElement
  
  // Remove existing theme classes
  root.classList.remove('light', 'dark')
  
  // Add the effective theme class
  root.classList.add(effectiveTheme)
  
  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]')
  const themeColors = {
    light: '#ffffff',
    dark: '#0a0a0a'
  }
  
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', themeColors[effectiveTheme])
  }
}

/**
 * Initialize theme system
 */
export function initializeTheme(): Theme {
  const storedTheme = getStoredTheme()
  applyTheme(storedTheme)
  return storedTheme
}

/**
 * Listen for system theme changes
 */
export function watchSystemTheme(callback: (systemTheme: 'light' | 'dark') => void): () => void {
  if (typeof window === 'undefined') return () => {}
  
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  
  const handler = (e: MediaQueryListEvent) => {
    callback(e.matches ? 'dark' : 'light')
  }
  
  mediaQuery.addEventListener('change', handler)
  
  // Return cleanup function
  return () => mediaQuery.removeEventListener('change', handler)
}