import { motion } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

export function ActionButton({
  icon: Icon,
  label,
  hint,
  onClick,
  tone = "ice",
}: {
  icon: LucideIcon
  label: string
  hint: string
  onClick?: () => void
  tone?: "ice" | "mint" | "flare"
}) {
  const colors = {
    ice: "hover:border-ice/50 hover:text-ice",
    mint: "hover:border-mint/50 hover:text-mint",
    flare: "hover:border-flare/50 hover:text-flare",
  }
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <motion.button
          type="button"
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.96 }}
          onClick={onClick}
          className={cn(
            "flex min-w-28 flex-col items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-slate-200",
            colors[tone],
          )}
        >
          <Icon className="h-5 w-5" />
          <span className="text-[10px] uppercase tracking-[0.18em]">{label}</span>
        </motion.button>
      </TooltipTrigger>
      <TooltipContent>{hint}</TooltipContent>
    </Tooltip>
  )
}
