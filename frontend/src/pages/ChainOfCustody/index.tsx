import { useEffect, useState } from "react"
import { Clock3, Fingerprint } from "lucide-react"
import { PageHeader } from "@/components/layout/PageHeader"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { chainOfCustodyApi } from "@/lib/api"
import { extractApiError, formatDate } from "@/lib/utils"
import { useWorkspace } from "@/hooks/useWorkspace"
import type { EvidenceCustody } from "@/types/api"

export default function ChainOfCustodyPage() {
  const { evidence, loading, error: evidenceError } = useWorkspace()
  const [selectedId, setSelectedId] = useState("")
  const [custody, setCustody] = useState<EvidenceCustody | null>(null)
  const [loadingEvents, setLoadingEvents] = useState(false)
  const [eventError, setEventError] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedId) {
      setCustody(null)
      setEventError(null)
      return
    }

    let active = true
    setLoadingEvents(true)
    setEventError(null)
    chainOfCustodyApi.getForEvidence(Number(selectedId))
      .then((response) => {
        if (active) setCustody(response.data)
      })
      .catch((err: unknown) => {
        if (active) setEventError(extractApiError(err))
      })
      .finally(() => {
        if (active) setLoadingEvents(false)
      })

    return () => {
      active = false
    }
  }, [selectedId])

  return (
    <div>
      <PageHeader
        kicker="Evidence history"
        title="Chain of Custody"
        detail="Review the recorded custody events for registered evidence, in chronological order."
      />
      <div className="glass-panel max-w-3xl space-y-5 p-5">
        <div>
          <p className="mb-2 text-xs uppercase tracking-[0.18em] text-slate-400">Select evidence</p>
          <Select value={selectedId} onValueChange={setSelectedId}>
            <SelectTrigger>
              <SelectValue placeholder={loading ? "Loading evidence…" : "Choose evidence"} />
            </SelectTrigger>
            <SelectContent>
              {evidence.map((item) => (
                <SelectItem key={item.id} value={String(item.id)}>
                  EVD-{item.id} · {item.file_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {evidenceError && <p role="alert" className="mt-2 text-sm text-flare">Evidence list unavailable: {evidenceError}</p>}
          {eventError && <p role="alert" className="mt-2 text-sm text-flare">Custody history unavailable: {eventError}</p>}
        </div>

        {loadingEvents && <p className="text-sm text-slate-400">Loading recorded events…</p>}
        {custody && (
          <>
            <section className="grid gap-4 rounded-lg border border-white/10 bg-black/20 p-4 sm:grid-cols-2">
              <div>
                <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Evidence ID</p>
                <p className="mt-1 font-mono text-sm text-ice">EVD-{custody.evidence_id}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Filename</p>
                <p className="mt-1 break-all text-sm text-slate-200">{custody.file_name}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Case</p>
                <p className="mt-1 text-sm text-slate-200">{custody.case_number} · CASE-{custody.case_id}</p>
              </div>
              <div className="sm:col-span-2">
                <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Original / Reference SHA-256</p>
                <p className="mt-1 break-all font-mono text-xs text-ice">{custody.reference_hash}</p>
              </div>
            </section>

            <section>
              <h2 className="mb-4 flex items-center gap-2 text-sm uppercase tracking-[0.18em] text-slate-300">
                <Clock3 className="h-4 w-4 text-ice" />
                Chronological custody events
              </h2>
              {custody.events.length ? (
                <ol className="space-y-4 border-l border-ice/20 pl-5">
                  {custody.events.map((event) => (
                    <li key={event.id} className="relative rounded-lg border border-white/10 bg-black/20 p-4">
                      <span className="absolute -left-[25px] top-5 h-2.5 w-2.5 rounded-full border border-ice bg-[#071018]" />
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-xs font-semibold uppercase tracking-wider text-ice">{event.action}</p>
                        <p className="text-xs text-slate-500">{formatDate(event.timestamp)}</p>
                      </div>
                      <p className="mt-2 text-sm text-slate-200">{event.description || "Custody event recorded."}</p>
                      <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
                        <Fingerprint className="h-3.5 w-3.5" />
                        {event.username} · EVD-{event.evidence_id}
                      </p>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-sm text-slate-500">No custody events have been recorded for this evidence.</p>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  )
}
