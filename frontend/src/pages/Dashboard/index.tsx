import { useCallback, useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { FileSearch, ShieldCheck, Upload } from "lucide-react"
import { ActionButton } from "@/components/forensic/ActionButton"
import { CaseTimeline } from "@/components/forensic/CaseTimeline"
import { EvidenceCard } from "@/components/forensic/EvidenceCard"
import { IntegrityStatus } from "@/components/forensic/IntegrityStatus"
import { StatPulse } from "@/components/forensic/StatPulse"
import { PageHeader } from "@/components/layout/PageHeader"
import { dashboardApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"
import type { DashboardSummary } from "@/types/api"
import { useWorkspace } from "@/hooks/useWorkspace"

export default function DashboardPage() {
  const { cases, evidence, audit, loading, error, reload } = useWorkspace()
  const navigate = useNavigate()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  const loadSummary = useCallback(async () => {
    setSummaryError(null)
    try {
      const response = await dashboardApi.summary()
      setSummary(response.data)
    } catch (err) {
      setSummaryError(extractApiError(err))
    }
  }, [])

  useEffect(() => {
    void loadSummary()
  }, [loadSummary])

  const recent = useMemo(() => [...evidence].sort((a, b) => b.uploaded_at.localeCompare(a.uploaded_at)).slice(0, 3), [evidence])
  const verificationEvents = audit.filter(
    (item) => item.action === "EVIDENCE_VERIFIED" || item.action === "EVIDENCE_VERIFICATION_FAILED",
  )
  const latestVerification = verificationEvents[0]
  const integrity = latestVerification
    ? latestVerification.action === "EVIDENCE_VERIFIED" ? "VERIFIED" : "FAILED"
    : "IDLE"

  return (
    <div>
      <PageHeader
        kicker="Digital Evidence Integrity System"
        title="Dashboard"
        detail="Register digital evidence, calculate SHA-256 hashes, review metadata, verify file integrity, and maintain case, audit, and report records."
      />
      {loading ? (
        <p className="text-sm text-slate-400">Loading dashboard data…</p>
      ) : error || summaryError ? (
        <div role="alert" className="glass-panel flex flex-wrap items-center justify-between gap-3 border-flare/30 p-5">
          <p className="text-sm text-flare">Dashboard data could not be loaded: {error || summaryError}</p>
          <button type="button" onClick={() => { void reload(); void loadSummary() }} className="text-xs uppercase tracking-wider text-ice hover:underline">
            Retry
          </button>
        </div>
      ) : !summary ? (
        <p className="text-sm text-slate-400">Loading dashboard data…</p>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-4 xl:grid-cols-7">
            <StatPulse label="Active Cases" value={summary.active_cases} hint={`${cases.length} total`} />
            <StatPulse label="Total Evidence" value={summary.total_evidence} />
            <StatPulse label="Verified" value={summary.verified_evidence} />
            <StatPulse label="Integrity Failed" value={summary.integrity_failed_evidence} />
            <StatPulse label="Pending Verification" value={summary.pending_verification} />
            <StatPulse label="Verification Records" value={summary.verification_records} />
            <StatPulse label="Audit Events" value={summary.audit_events} />
          </div>
          <div className="mt-6 grid gap-6 xl:grid-cols-[280px_1fr_1fr]">
            <div className="glass-panel p-4">
              <IntegrityStatus status={integrity} count={summary.verified_evidence} total={summary.total_evidence} />
            </div>
            <div className="space-y-4">
              <div className="flex gap-3">
                <ActionButton icon={Upload} label="Upload Evidence" hint="Add evidence to a case" onClick={() => navigate("/upload")} />
                <ActionButton icon={ShieldCheck} label="Verify Integrity" hint="Compare SHA-256 values" onClick={() => navigate("/verify")} tone="mint" />
                <ActionButton icon={FileSearch} label="View Metadata" hint="Review extracted file information" onClick={() => navigate("/metadata")} />
              </div>
              <div className="glass-panel p-5">
                <h2 className="mb-4 text-sm uppercase tracking-[0.2em] text-slate-400">Recent Evidence</h2>
                <div className="space-y-3">
                  {recent.length ? recent.map((item) => <EvidenceCard key={item.id} evidence={item} />) : <p className="text-sm text-slate-500">No evidence has been uploaded yet.</p>}
                </div>
              </div>
            </div>
            <div className="glass-panel p-5">
              <h2 className="mb-4 text-sm uppercase tracking-[0.2em] text-slate-400">Recent Activity</h2>
              <CaseTimeline logs={audit.slice(0, 8)} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
