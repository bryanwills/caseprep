import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ThemeToggle } from '@/components/common/theme-toggle'
import { 
  Shield, 
  Zap, 
  FileText, 
  Users, 
  Clock, 
  CheckCircle,
  ArrowRight,
  Play,
  Mic,
  FileAudio,
  Settings,
  Download,
  Eye,
  Menu
} from 'lucide-react'

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container-responsive flex h-16 items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-legal rounded-lg flex items-center justify-center">
              <FileAudio className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">CasePrep</span>
          </div>
          
          <div className="flex items-center space-x-4">
            <nav className="hidden md:flex items-center space-x-6">
              <Link href="#features" className="text-sm font-medium hover:text-primary transition-colors">
                Features
              </Link>
              <Link href="#pricing" className="text-sm font-medium hover:text-primary transition-colors">
                Pricing
              </Link>
              <Link href="#security" className="text-sm font-medium hover:text-primary transition-colors">
                Security
              </Link>
              <Link href="/auth/sign-in" className="text-sm font-medium hover:text-primary transition-colors">
                Sign In
              </Link>
              <Button asChild size="sm">
                <Link href="/auth/sign-up">Start Free Trial</Link>
              </Button>
            </nav>
            
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* Mobile Menu Button */}
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="py-12 md:py-24 lg:py-32">
          <div className="container-responsive">
            <div className="mx-auto max-w-4xl text-center">
              <Badge variant="secondary" className="mb-4">
                Privacy-First Legal Technology
              </Badge>
              
              <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl text-balance">
                Transform Legal{' '}
                <span className="text-transparent bg-clip-text gradient-legal">
                  Evidence Processing
                </span>
              </h1>
              
              <p className="mx-auto max-w-2xl text-muted-foreground text-lg sm:text-xl mt-6 text-balance">
                Extract and analyze audio/video evidence with AI transcription, speaker diarization, 
                and secure case preparation workflows. Built for legal professionals who demand 
                accuracy and privacy.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
                <Button size="lg" asChild className="text-lg px-8">
                  <Link href="/auth/sign-up">
                    Start Free Trial
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Link>
                </Button>
                
                <Button size="lg" variant="outline" asChild className="text-lg px-8">
                  <Link href="#demo">
                    <Play className="mr-2 w-5 h-5" />
                    Watch Demo
                  </Link>
                </Button>
              </div>
              
              <div className="flex items-center justify-center gap-8 mt-12 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-green-600" />
                  <span>SOC 2 Compliant</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>HIPAA Ready</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-green-600" />
                  <span>99.9% Uptime</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-12 md:py-24 bg-muted/50">
          <div className="container-responsive">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                Everything You Need for Legal Transcription
              </h2>
              <p className="text-muted-foreground text-lg mt-4 max-w-2xl mx-auto">
                Professional-grade features designed specifically for legal professionals
              </p>
            </div>
            
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {/* Core Features */}
              <Card className="relative overflow-hidden">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <Mic className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>AI Transcription</CardTitle>
                  <CardDescription>
                    Faster-Whisper large-v3 for industry-leading accuracy on legal content
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    <li>• 95%+ accuracy on clear audio</li>
                    <li>• Legal terminology optimized</li>
                    <li>• Real-time processing</li>
                    <li>• Multiple file formats</li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <Users className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>Speaker Identification</CardTitle>
                  <CardDescription>
                    Automatic speaker diarization with manual refinement capabilities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    <li>• AI-powered speaker detection</li>
                    <li>• Custom speaker labeling</li>
                    <li>• Color-coded transcripts</li>
                    <li>• Timeline synchronization</li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <FileText className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>Interactive Editor</CardTitle>
                  <CardDescription>
                    Real-time transcript editing with media synchronization
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    <li>• Click-to-seek playback</li>
                    <li>• Confidence indicators</li>
                    <li>• Find & replace tools</li>
                    <li>• Collaborative editing</li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <Shield className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>Privacy First</CardTitle>
                  <CardDescription>
                    Zero storage by default with enterprise-grade security
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    <li>• No data stored by default</li>
                    <li>• End-to-end encryption</li>
                    <li>• Chain of custody</li>
                    <li>• HIPAA/SOC 2 compliant</li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <Download className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>Multiple Exports</CardTitle>
                  <CardDescription>
                    Professional export formats for every legal workflow
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    <li>• PDF Quote Packs</li>
                    <li>• DOCX & SRT formats</li>
                    <li>• Embedded audit trails</li>
                    <li>• Digital signatures</li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <Settings className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>Smart Features</CardTitle>
                  <CardDescription>
                    Advanced tools that learn and adapt to your workflow
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    <li>• Custom dictionaries</li>
                    <li>• Learning corrections</li>
                    <li>• Smart clipping</li>
                    <li>• Bulk operations</li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-12 md:py-24">
          <div className="container-responsive">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                Transparent Pricing for Legal Teams
              </h2>
              <p className="text-muted-foreground text-lg mt-4 max-w-2xl mx-auto">
                Choose the plan that fits your practice. All plans include core features.
              </p>
            </div>
            
            <div className="grid gap-6 md:grid-cols-3 max-w-5xl mx-auto">
              {/* Starter Plan */}
              <Card className="relative">
                <CardHeader className="text-center pb-8">
                  <CardTitle className="text-2xl">Starter</CardTitle>
                  <CardDescription>Perfect for solo practitioners</CardDescription>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">$29</span>
                    <span className="text-muted-foreground">/month</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">10 hours of processing/month</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">AI transcription & diarization</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">All export formats</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Email support</span>
                    </div>
                  </div>
                  <Button className="w-full" variant="outline">
                    Start Free Trial
                  </Button>
                </CardContent>
              </Card>

              {/* Professional Plan */}
              <Card className="relative border-primary shadow-lg">
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge>Most Popular</Badge>
                </div>
                <CardHeader className="text-center pb-8">
                  <CardTitle className="text-2xl">Professional</CardTitle>
                  <CardDescription>For growing legal teams</CardDescription>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">$99</span>
                    <span className="text-muted-foreground">/month</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">50 hours of processing/month</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Everything in Starter</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Team collaboration</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Priority support</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Custom branding</span>
                    </div>
                  </div>
                  <Button className="w-full">
                    Start Free Trial
                  </Button>
                </CardContent>
              </Card>

              {/* Enterprise Plan */}
              <Card className="relative">
                <CardHeader className="text-center pb-8">
                  <CardTitle className="text-2xl">Enterprise</CardTitle>
                  <CardDescription>For large firms and organizations</CardDescription>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">$299</span>
                    <span className="text-muted-foreground">/month</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Unlimited processing</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Everything in Professional</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">SSO & advanced security</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Dedicated support</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm">Custom integrations</span>
                    </div>
                  </div>
                  <Button className="w-full" variant="outline">
                    Contact Sales
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t bg-muted/50 py-12">
        <div className="container-responsive">
          <div className="grid gap-8 md:grid-cols-4">
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-legal rounded-lg flex items-center justify-center">
                  <FileAudio className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold">CasePrep</span>
              </div>
              <p className="text-sm text-muted-foreground max-w-xs">
                Privacy-first legal transcription platform built for modern legal professionals.
              </p>
            </div>
            
            <div className="space-y-4">
              <h4 className="font-semibold">Product</h4>
              <div className="space-y-2">
                <Link href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Features
                </Link>
                <Link href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Pricing
                </Link>
                <Link href="/integrations" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Integrations
                </Link>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className="font-semibold">Company</h4>
              <div className="space-y-2">
                <Link href="/about" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  About
                </Link>
                <Link href="/contact" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Contact
                </Link>
                <Link href="/careers" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Careers
                </Link>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className="font-semibold">Legal</h4>
              <div className="space-y-2">
                <Link href="/privacy" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Privacy Policy
                </Link>
                <Link href="/terms" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Terms of Service
                </Link>
                <Link href="/security" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Security
                </Link>
              </div>
            </div>
          </div>
          
          <div className="border-t pt-8 mt-8 flex flex-col sm:flex-row justify-between items-center">
            <p className="text-sm text-muted-foreground">
              © 2024 CasePrep. All rights reserved.
            </p>
            <div className="flex items-center space-x-4 mt-4 sm:mt-0">
              <Badge variant="outline" className="text-xs">
                <Shield className="w-3 h-3 mr-1" />
                SOC 2 Compliant
              </Badge>
              <Badge variant="outline" className="text-xs">
                <Eye className="w-3 h-3 mr-1" />
                HIPAA Ready
              </Badge>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}