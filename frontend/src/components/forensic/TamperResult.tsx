import { motion } from "framer-motion"
import { ShieldAlert, ShieldCheck, Unplug } from "lucide-react"
import type { VerificationResult } from "@/types/api"
import { HashComparison } from "@/components/forensic/HashComparison"
import { formatDate } from "@/lib/utils"

export function TamperResult({ result }: { result: VerificationResult }) {
  const failed = result.verification_status === "FAILED"
  const missing = result.verification_status === "MISSING"

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className={
        failed || missing
          ? "rounded-xl border border-flare/50 bg-flare/10 p-6"
          : "rounded-xl border border-mint/40 bg-mint/10 p-6"
      }
    >
      <div className="mb-4 flex items-center gap-3">
        {failed ? (
          <ShieldAlert className="h-8 w-8 text-flare" />
        ) : missing ? (
          <Unplug className="h-8 w-8 text-amber-300" />
        ) : (
          <ShieldCheck className="h-8 w-8 text-mint" />
        )}
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400">Integrity verdict</p>
          <p className={`text-3xl font-bold tracking-[0.18em] ${failed || missing ? "text-flare" : "text-mint"}`}>
            {failed ? "INTEGRITY FAILED" : missing ? "MISSING" : "VERIFIED"}
          </p>
        </div>
      </div>
      <p className="mb-5 text-sm text-slate-200">{result.message}</p>
      <HashComparison stored={result.stored_hash} current={result.current_hash} />
      <p className="mt-4 text-xs text-slate-500">Checked {formatDate(result.verified_at)}</p>
    </motion.div>
  )
}
