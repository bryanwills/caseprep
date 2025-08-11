'use client'

import * as React from 'react'
import { initializeTheme } from '@/lib/theme'

interface ThemeProviderProps {
  children: React.ReactNode
}

/**
 * Theme provider that handles theme initialization and SSR
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    // Initialize theme system
    initializeTheme()
    setMounted(true)
  }, [])

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return <div style={{ visibility: 'hidden' }}>{children}</div>
  }

  return <>{children}</>
}

/**
 * Theme script to prevent flash of wrong theme
 * This should be included in the document head
 */
export function ThemeScript() {
  const script = `
    (function() {
      try {
        var theme = localStorage.getItem('caseprep-theme') || 'system';
        var systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        var effectiveTheme = theme === 'system' ? systemTheme : theme;
        
        document.documentElement.classList.remove('light', 'dark');
        document.documentElement.classList.add(effectiveTheme);
        
        // Update meta theme-color
        var metaThemeColor = document.querySelector('meta[name="theme-color"]');
        var colors = { light: '#ffffff', dark: '#0a0a0a' };
        if (metaThemeColor) {
          metaThemeColor.setAttribute('content', colors[effectiveTheme]);
        }
      } catch (e) {
        // Fallback to light theme
        document.documentElement.classList.add('light');
      }
    })();
  `;

  return <script dangerouslySetInnerHTML={{ __html: script }} />
}