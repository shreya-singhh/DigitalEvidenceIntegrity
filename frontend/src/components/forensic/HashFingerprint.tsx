import { motion } from "framer-motion"
import { Check, Copy } from "lucide-react"
import { useState } from "react"
import { cn, chunkHash } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

export function HashFingerprint({ hash, className }: { hash: string; className?: string }) {
  const [copied, setCopied] = useState(false)
  const chunks = chunkHash(hash)

  async function copy() {
    await navigator.clipboard.writeText(hash)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1400)
  }

  return (
    <div className={cn("group flex items-start gap-2", className)}>
      <div className="flex flex-wrap gap-1 font-mono text-[11px] leading-5 tracking-[0.16em] text-ice/90">
        {chunks.map((chunk, index) => (
          <span key={`${chunk}-${index}`} className="rounded-sm bg-ice/5 px-1 py-0.5">
            {chunk}
          </span>
        ))}
      </div>
      <Tooltip>
        <TooltipTrigger asChild>
          <motion.button
            type="button"
            whileTap={{ scale: 0.9 }}
            onClick={copy}
            className="mt-0.5 rounded-md border border-white/10 p-1 text-slate-400 hover:border-ice/40 hover:text-ice"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-mint" /> : <Copy className="h-3.5 w-3.5" />}
          </motion.button>
        </TooltipTrigger>
        <TooltipContent>{copied ? "Copied SHA-256" : "Copy fingerprint"}</TooltipContent>
      </Tooltip>
    </div>
  )
}
