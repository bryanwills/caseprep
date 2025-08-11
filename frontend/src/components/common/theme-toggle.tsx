'use client'

import * as React from 'react'
import { Monitor, Moon, Sun } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useTheme } from '@/hooks/use-theme'
import { cn } from '@/lib/utils'

interface ThemeToggleProps {
  className?: string
  variant?: 'default' | 'ghost' | 'outline'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

export function ThemeToggle({ 
  className, 
  variant = 'ghost', 
  size = 'icon' 
}: ThemeToggleProps) {
  const { theme, setTheme, themes } = useTheme()

  const getThemeIcon = (themeName: string, isActive: boolean) => {
    const iconProps = {
      className: cn(
        'h-4 w-4 transition-all',
        isActive ? 'text-primary' : 'text-muted-foreground'
      )
    }

    switch (themeName) {
      case 'light':
        return <Sun {...iconProps} />
      case 'dark':
        return <Moon {...iconProps} />
      case 'system':
        return <Monitor {...iconProps} />
      default:
        return <Monitor {...iconProps} />
    }
  }

  const getCurrentIcon = () => {
    switch (theme) {
      case 'light':
        return <Sun className="h-4 w-4" />
      case 'dark':
        return <Moon className="h-4 w-4" />
      case 'system':
      default:
        return <Monitor className="h-4 w-4" />
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          size={size}
          className={cn(
            'touch-target transition-colors hover:bg-accent hover:text-accent-foreground',
            className
          )}
          aria-label={`Current theme: ${theme}. Click to change theme`}
        >
          {getCurrentIcon()}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[160px]">
        {themes.map((themeOption) => (
          <DropdownMenuItem
            key={themeOption.value}
            onClick={() => setTheme(themeOption.value)}
            className={cn(
              'flex items-center gap-2 cursor-pointer',
              theme === themeOption.value && 'bg-accent text-accent-foreground'
            )}
          >
            {getThemeIcon(themeOption.value, theme === themeOption.value)}
            <div className="flex flex-col">
              <span className="text-sm font-medium">{themeOption.label}</span>
              <span className="text-xs text-muted-foreground">
                {themeOption.description}
              </span>
            </div>
            {theme === themeOption.value && (
              <div className="ml-auto h-2 w-2 rounded-full bg-primary" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/**
 * Compact theme toggle for mobile or small spaces
 */
export function CompactThemeToggle({ className }: { className?: string }) {
  const { toggleTheme, theme } = useTheme()

  const getCurrentIcon = () => {
    switch (theme) {
      case 'light':
        return <Sun className="h-4 w-4" />
      case 'dark':
        return <Moon className="h-4 w-4" />
      case 'system':
      default:
        return <Monitor className="h-4 w-4" />
    }
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className={cn('touch-target', className)}
      aria-label={`Current theme: ${theme}. Click to cycle through themes`}
    >
      {getCurrentIcon()}
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}