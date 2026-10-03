import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-md border border-white/10 bg-[#081018] px-3 py-2 text-sm text-slate-100 shadow-inner outline-none transition placeholder:text-slate-500 focus:border-ice/50 focus:ring-2 focus:ring-ice/20",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
)
Input.displayName = "Input"

export { Input }
