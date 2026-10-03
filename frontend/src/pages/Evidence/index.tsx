import { useMemo, useState } from "react"
import { EvidenceCard } from "@/components/forensic/EvidenceCard"
import { PageHeader } from "@/components/layout/PageHeader"
import { Input } from "@/components/ui/input"
import { useWorkspace } from "@/hooks/useWorkspace"

export default function EvidencePage() {
  const { cases, evidence, loading, error, reload } = useWorkspace()
  const [q, setQ] = useState("")
  const caseMap = useMemo(() => new Map(cases.map((c) => [c.id, c.case_number])), [cases])
  const filtered = evidence.filter(
    (item) =>
      item.file_name.toLowerCase().includes(q.toLowerCase()) ||
      item.sha256_hash.toLowerCase().includes(q.toLowerCase()),
  )

  return (
    <div>
      <PageHeader
        kicker="Evidence records"
        title="Evidence"
        detail="Authenticated evidence index showing records attached to your cases."
      />
      <Input className="mb-6 max-w-md" placeholder="Filter by filename or SHA-256" value={q} onChange={(e) => setQ(e.target.value)} />
      {loading ? (
        <p className="text-sm text-slate-400">Loading evidence…</p>
      ) : error ? (
        <div role="alert" className="glass-panel flex flex-wrap items-center justify-between gap-3 border-flare/30 p-5">
          <p className="text-sm text-flare">Evidence index unavailable: {error}</p>
          <button type="button" onClick={() => void reload()} className="text-xs uppercase tracking-wider text-ice hover:underline">
            Retry
          </button>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {filtered.map((item) => (
            <EvidenceCard key={item.id} evidence={item} caseNumber={caseMap.get(item.case_id)} />
          ))}
          {!filtered.length && <p className="text-sm text-slate-500">No matching evidence.</p>}
        </div>
      )}
    </div>
  )
}
