import type { Metadata, Viewport } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import { cn } from '@/lib/utils'
import { ThemeProvider, ThemeScript } from '@/components/common/theme-provider'
import '@/styles/globals.css'

// Fonts
const fontSans = Inter({
  subsets: ['latin'],
  variable: '--font-geist-sans',
  display: 'swap',
})

const fontMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-geist-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: {
    default: 'CasePrep - Legal Transcription & Case Preparation',
    template: '%s | CasePrep'
  },
  description: 'Privacy-first legal transcription tool for evidence processing. Extract and analyze audio/video evidence with AI transcription, speaker diarization, and secure case preparation workflows.',
  keywords: [
    'legal transcription',
    'case preparation', 
    'evidence processing',
    'court transcription',
    'legal technology',
    'AI transcription',
    'speaker identification',
    'secure transcription'
  ],
  authors: [
    {
      name: 'CasePrep Team',
      url: 'https://caseprep.com',
    },
  ],
  creator: 'CasePrep',
  publisher: 'CasePrep',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: '/',
    title: 'CasePrep - Legal Transcription & Case Preparation',
    description: 'Privacy-first legal transcription tool for evidence processing',
    siteName: 'CasePrep',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'CasePrep - Legal Transcription Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CasePrep - Legal Transcription & Case Preparation',
    description: 'Privacy-first legal transcription tool for evidence processing',
    images: ['/twitter-image.png'],
    creator: '@caseprep',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: process.env.GOOGLE_SITE_VERIFICATION,
    yandex: process.env.YANDEX_VERIFICATION,
    yahoo: process.env.YAHOO_SITE_VERIFICATION,
  },
  category: 'legal technology',
  classification: 'business',
  referrer: 'origin-when-cross-origin',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0a0a' },
  ],
  colorScheme: 'light dark',
  viewportFit: 'cover',
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Theme script to prevent flash */}
        <ThemeScript />
        
        {/* Preload critical resources */}
        <link
          rel="preload" 
          href="/fonts/legal-serif.woff2" 
          as="font" 
          type="font/woff2" 
          crossOrigin="anonymous"
        />
        
        {/* PWA manifest */}
        <link rel="manifest" href="/manifest.json" />
        
        {/* Apple PWA meta tags */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="CasePrep" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        
        {/* Favicon */}
        <link rel="icon" href="/favicon.ico" sizes="32x32" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        
        {/* Theme color meta (will be updated by theme system) */}
        <meta name="theme-color" content="#ffffff" />
        
        {/* Security headers */}
        <meta httpEquiv="X-Content-Type-Options" content="nosniff" />
        <meta httpEquiv="X-Frame-Options" content="DENY" />
        <meta httpEquiv="X-XSS-Protection" content="1; mode=block" />
        <meta 
          httpEquiv="Strict-Transport-Security" 
          content="max-age=31536000; includeSubDomains" 
        />
        <meta 
          httpEquiv="Content-Security-Policy" 
          content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: ws:; media-src 'self' blob:; object-src 'none'; base-uri 'self';" 
        />
      </head>
      <body
        className={cn(
          'min-h-screen bg-background font-sans antialiased',
          'safe-top safe-bottom safe-left safe-right',
          fontSans.variable,
          fontMono.variable
        )}
        suppressHydrationWarning
      >
        <ThemeProvider>
          {/* Skip to main content for accessibility */}
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 bg-primary text-primary-foreground px-4 py-2 rounded-md"
          >
            Skip to main content
          </a>
          
          {/* Main application */}
          <div id="main-content" className="relative">
            {children}
          </div>
          
          {/* Screen reader announcements */}
          <div
            id="announcements"
            aria-live="polite"
            aria-atomic="true"
            className="sr-only"
          />
        </ThemeProvider>
      </body>
    </html>
  )
}