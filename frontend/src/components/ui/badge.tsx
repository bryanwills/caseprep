import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        // Status badges for transcription workflow
        processing: 
          "border-transparent bg-status-processing text-white",
        completed: 
          "border-transparent bg-status-completed text-white",
        error: 
          "border-transparent bg-status-error text-white",
        pending: 
          "border-transparent bg-status-pending text-white",
        // Legal industry specific badges
        confidential: 
          "border-transparent bg-legal-accent text-white",
        privileged: 
          "border-transparent bg-legal-primary text-white",
        // Confidence level badges
        "high-confidence": 
          "border-transparent bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
        "medium-confidence": 
          "border-transparent bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
        "low-confidence": 
          "border-transparent bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }