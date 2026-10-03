import { motion } from "framer-motion"
import { ShieldAlert, ShieldCheck } from "lucide-react"
import { cn } from "@/lib/utils"
import type { VerificationStatus } from "@/types/api"

const labels: Record<VerificationStatus | "IDLE", string> = {
  VERIFIED: "VERIFIED",
  FAILED: "INTEGRITY FAILED",
  MISSING: "MISSING",
  IDLE: "Verification Status",
}

export function IntegrityStatus({
  status = "IDLE",
  count,
  total,
}: {
  status?: VerificationStatus | "IDLE"
  count?: number
  total?: number
}) {
  const tone =
    status === "VERIFIED" ? "text-mint border-mint/40" : status === "FAILED" ? "text-flare border-flare/50" : "text-ice border-ice/30"

  return (
    <div className="relative mx-auto flex h-64 w-64 items-center justify-center">
      <motion.div
        className="absolute inset-0 rounded-full border border-white/10"
        animate={{ rotate: 360 }}
        transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className={cn("absolute inset-4 rounded-full border border-dashed", tone)}
        animate={{ rotate: -360 }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
      />
      <div className="absolute inset-8 rounded-full bg-[#071018] shadow-[inset_0_0_40px_rgba(110,231,255,0.08)]" />
      <div className="relative z-10 text-center">
        {status === "FAILED" ? (
          <ShieldAlert className="mx-auto mb-2 h-8 w-8 text-flare" />
        ) : (
          <ShieldCheck className="mx-auto mb-2 h-8 w-8 text-ice" />
        )}
        <p
          className={cn(
            "font-bold",
            status === "FAILED"
              ? "max-w-40 text-sm leading-5 tracking-wider"
              : "text-2xl tracking-[0.24em]",
            tone.split(" ")[0],
          )}
        >
          {labels[status]}
        </p>
        {typeof count === "number" && typeof total === "number" && (
          <p className="mt-2 font-mono text-xs text-slate-400">
            {count}/{total} evidence records verified
          </p>
        )}
      </div>
    </div>
  )
}
