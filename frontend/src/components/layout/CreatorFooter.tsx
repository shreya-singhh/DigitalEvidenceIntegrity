import { cn } from "@/lib/utils"

export function CreatorFooter({ className }: { className?: string }) {
  return (
    <footer className={cn("text-center text-xs text-slate-500", className)}>
      © 2026 Shreya Singh | Digital Evidence Integrity System
    </footer>
  )
}
