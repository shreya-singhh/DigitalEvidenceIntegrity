import * as React from "react"
import { cn } from "@/lib/utils"

const Textarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<"textarea">>(
  ({ className, ...props }, ref) => (
    <textarea
      className={cn(
        "flex min-h-24 w-full rounded-md border border-white/10 bg-[#081018] px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-ice/50 focus:ring-2 focus:ring-ice/20",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
)
Textarea.displayName = "Textarea"

export { Textarea }
