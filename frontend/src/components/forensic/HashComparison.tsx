import { motion } from "framer-motion"
import { chunkHash } from "@/lib/utils"

export function HashComparison({ stored, current }: { stored: string; current?: string | null }) {
  const storedChunks = chunkHash(stored, 2)
  const currentChunks = chunkHash(current || "", 2)
  const max = Math.max(storedChunks.length, currentChunks.length, 1)

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <HashColumn label="Stored / reference SHA-256" chunks={storedChunks} compare={currentChunks} />
      <HashColumn label="Live SHA-256" chunks={currentChunks} compare={storedChunks} missing={!current} />
      <p className="md:col-span-2 font-mono text-xs text-slate-500">Compared {max * 2} hex characters across SHA-256.</p>
    </div>
  )
}

function HashColumn({
  label,
  chunks,
  compare,
  missing,
}: {
  label: string
  chunks: string[]
  compare: string[]
  missing?: boolean
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-black/30 p-4">
      <p className="mb-3 text-[10px] uppercase tracking-[0.2em] text-slate-400">{label}</p>
      {missing ? (
        <p className="text-flare">File missing from storage</p>
      ) : (
        <div className="flex flex-wrap gap-1 font-mono text-xs">
          {chunks.map((chunk, i) => {
            const match = compare[i] === chunk
            return (
              <motion.span
                key={`${label}-${i}`}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.012 }}
                className={match ? "text-mint" : "rounded-sm bg-flare/15 px-0.5 text-flare"}
              >
                {chunk}
              </motion.span>
            )
          })}
        </div>
      )}
    </div>
  )
}
