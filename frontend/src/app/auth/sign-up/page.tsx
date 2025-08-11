import Link from 'next/link'
import { Metadata } from 'next'
import { ArrowLeft, Github, Mail, Building2, User } from 'lucide-react'
import { FaGoogle, FaFacebook } from 'react-icons/fa'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ThemeToggle } from '@/components/common/theme-toggle'

export const metadata: Metadata = {
  title: 'Sign Up',
  description: 'Create your CasePrep account',
}

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container-responsive flex h-16 items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/" className="flex items-center space-x-2">
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </Link>
            </Button>
            
            <div className="h-6 w-px bg-border" />
            
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-gradient-legal rounded-md flex items-center justify-center">
                <span className="text-xs font-bold text-white">C</span>
              </div>
              <span className="font-semibold">CasePrep</span>
            </Link>
          </div>
          
          <ThemeToggle />
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center py-12 px-4">
        <div className="w-full max-w-md">
          <Card className="shadow-legal-lg">
            <CardHeader className="space-y-1 text-center">
              <CardTitle className="text-2xl font-bold">Get started</CardTitle>
              <CardDescription>
                Create your account and start transcribing in minutes
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* Social Login Buttons */}
              <div className="space-y-3">
                <Button variant="outline" className="w-full" size="mobile-sm">
                  <FaGoogle className="w-4 h-4 mr-2 text-red-500" />
                  Continue with Google
                </Button>
                
                <Button variant="outline" className="w-full" size="mobile-sm">
                  <Github className="w-4 h-4 mr-2" />
                  Continue with GitHub
                </Button>
                
                <Button variant="outline" className="w-full" size="mobile-sm">
                  <FaFacebook className="w-4 h-4 mr-2 text-blue-600" />
                  Continue with Facebook
                </Button>
              </div>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    Or continue with email
                  </span>
                </div>
              </div>

              {/* Email Form */}
              <form className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First name</Label>
                    <Input
                      id="firstName"
                      type="text"
                      placeholder="John"
                      autoComplete="given-name"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last name</Label>
                    <Input
                      id="lastName"
                      type="text"
                      placeholder="Doe"
                      autoComplete="family-name"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Work email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="john.doe@lawfirm.com"
                    autoComplete="email"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="firmName">Law firm / Organization</Label>
                  <Input
                    id="firmName"
                    type="text"
                    placeholder="Doe & Associates"
                    autoComplete="organization"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Create a strong password"
                    autoComplete="new-password"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Must be at least 8 characters with numbers and symbols
                  </p>
                </div>

                <Button type="submit" className="w-full" size="mobile-sm">
                  <User className="w-4 h-4 mr-2" />
                  Create account
                </Button>
              </form>

              {/* Sign in link */}
              <div className="text-center text-sm">
                <span className="text-muted-foreground">Already have an account? </span>
                <Link href="/auth/sign-in" className="text-primary hover:underline font-medium">
                  Sign in
                </Link>
              </div>

              {/* Legal text */}
              <div className="text-xs text-center text-muted-foreground">
                <p>
                  By creating an account, you agree to our{' '}
                  <Link href="/terms" className="underline hover:text-foreground">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link href="/privacy" className="underline hover:text-foreground">
                    Privacy Policy
                  </Link>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Trust indicators */}
          <div className="mt-8 space-y-4">
            <div className="flex justify-center space-x-4 text-xs text-muted-foreground">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span>SOC 2 Compliant</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span>256-bit Encryption</span>
              </div>
            </div>
            
            <div className="text-center text-xs text-muted-foreground">
              <p>🎉 <strong>Free trial:</strong> 14 days with full access, no credit card required</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}