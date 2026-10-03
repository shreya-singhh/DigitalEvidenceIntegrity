import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { toast } from "sonner"
import { PageHeader } from "@/components/layout/PageHeader"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { auditApi } from "@/lib/api"
import { extractApiError, formatDate } from "@/lib/utils"
import type { AuditLog } from "@/types/api"

export default function AuditPage() {
  const [params] = useSearchParams()
  const evidenceId = params.get("evidenceId")
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [skip, setSkip] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const limit = 50

  async function load(nextSkip: number) {
    setLoading(true)
    setError(null)
    try {
      const res = evidenceId
        ? await auditApi.byEvidence(Number(evidenceId), nextSkip, limit)
        : await auditApi.list(nextSkip, limit)
      setLogs(res.data)
      setSkip(nextSkip)
    } catch (err) {
      const message = extractApiError(err)
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load(0)
  }, [evidenceId])

  return (
    <div>
      <PageHeader
        kicker="System records"
        title="Audit Logs"
        detail={evidenceId ? `Showing events for evidence record EVD-${evidenceId}.` : "Review recorded activity from the system."}
      />
      <div className="overflow-x-auto rounded-xl border border-white/10">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-white/5 text-[10px] uppercase tracking-[0.18em] text-slate-500">
            <tr>
              <th className="px-4 py-3">When</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Scope</th>
              <th className="px-4 py-3">Detail</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td className="px-4 py-6 text-center text-slate-400" colSpan={4}>Loading audit events…</td></tr>
            )}
            {!loading && error && (
              <tr><td role="alert" className="px-4 py-6 text-center text-flare" colSpan={4}>{error}</td></tr>
            )}
            {!loading && !error && logs.map((log) => (
              <tr key={log.id} className="border-t border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 font-mono text-xs text-slate-400">{formatDate(log.created_at)}</td>
                <td className="px-4 py-3">
                  <Badge>{log.action}</Badge>
                </td>
                <td className="px-4 py-3 text-xs">
                  {log.case_id ? (
                    <Link className="text-ice hover:underline" to={`/cases/${log.case_id}`}>
                      CASE-{log.case_id}
                    </Link>
                  ) : null}
                  {log.evidence_id ? (
                    <>
                      {" "}
                      <Link className="text-ice hover:underline" to={`/evidence/${log.evidence_id}`}>
                        EVD-{log.evidence_id}
                      </Link>
                    </>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-slate-300">{log.description}</td>
              </tr>
            ))}
            {!loading && !error && !logs.length && (
              <tr><td className="px-4 py-6 text-center text-slate-500" colSpan={4}>No audit events have been recorded.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex gap-2">
        <Button variant="outline" disabled={loading || skip === 0} onClick={() => load(Math.max(0, skip - limit))}>
          Previous
        </Button>
        <Button variant="outline" disabled={loading || logs.length < limit} onClick={() => load(skip + limit)}>
          Next
        </Button>
      </div>
    </div>
  )
}
