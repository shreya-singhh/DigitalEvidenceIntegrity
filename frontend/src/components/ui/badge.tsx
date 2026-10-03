import type { HTMLAttributes } from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-sm border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em]",
  {
    variants: {
      variant: {
        default: "border-ice/30 bg-ice/10 text-ice",
        muted: "border-white/10 bg-white/5 text-slate-300",
        success: "border-mint/30 bg-mint/10 text-mint",
        danger: "border-flare/40 bg-flare/10 text-flare",
        warn: "border-amber-400/30 bg-amber-400/10 text-amber-200",
      },
    },
    defaultVariants: { variant: "default" },
  },
)

export function Badge({
  className,
  variant,
  ...props
}: HTMLAttributes<HTMLDivElement> & VariantProps<typeof badgeVariants>) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}
