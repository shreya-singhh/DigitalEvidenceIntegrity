import { motion, useMotionValue, useTransform, animate } from "framer-motion"
import { useEffect } from "react"

export function StatPulse({ label, value, hint }: { label: string; value: number; hint?: string }) {
  const count = useMotionValue(0)
  const rounded = useTransform(count, (latest) => Math.round(latest).toString())

  useEffect(() => {
    const controls = animate(count, value, { duration: 0.9, ease: "easeOut" })
    return controls.stop
  }, [count, value])

  return (
    <div className="glass-panel p-4">
      <p className="relative z-10 text-[10px] uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <motion.p className="relative z-10 mt-2 font-mono text-3xl text-ice">{rounded}</motion.p>
      {hint && <p className="relative z-10 mt-1 text-xs text-slate-500">{hint}</p>}
      <span className="absolute right-4 top-4 h-2 w-2 animate-pulse rounded-full bg-mint" />
    </div>
  )
}
