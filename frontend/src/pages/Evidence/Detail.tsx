import { useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { Download, FileSearch, ScrollText, ShieldCheck } from "lucide-react"
import { toast } from "sonner"
import { ActionButton } from "@/components/forensic/ActionButton"
import { CaseTimeline } from "@/components/forensic/CaseTimeline"
import { HashFingerprint } from "@/components/forensic/HashFingerprint"
import { PageHeader } from "@/components/layout/PageHeader"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { auditApi, casesApi, evidenceApi } from "@/lib/api"
import { extractApiError, formatBytes, formatDate } from "@/lib/utils"
import type { AuditLog, CaseRecord, EvidenceRecord, VerificationResult } from "@/types/api"

export default function EvidenceDetailPage() {
  const { evidenceId } = useParams()
  const id = Number(evidenceId)
  const navigate = useNavigate()
  const [record, setRecord] = useState<EvidenceRecord | null>(null)
  const [caseRecord, setCaseRecord] = useState<CaseRecord | null>(null)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [integrity, setIntegrity] = useState<VerificationResult | null>(null)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    if (!Number.isFinite(id)) return
    void (async () => {
      try {
        const ev = await evidenceApi.get(id)
        setRecord(ev.data)
        const [cs, lg, check] = await Promise.all([
          casesApi.get(ev.data.case_id),
          auditApi.byEvidence(id, 0, 80),
          evidenceApi.integrity(id),
        ])
        setCaseRecord(cs.data)
        setLogs(lg.data)
        setIntegrity(check.data)
      } catch (err) {
        toast.error(extractApiError(err))
      }
    })()
  }, [id])

  async function downloadOriginal() {
    if (!record) return
    setDownloading(true)
    try {
      const response = await evidenceApi.download(record.id)
      const url = URL.createObjectURL(response.data)
      const link = document.createElement("a")
      link.href = url
      link.download = record.file_name
      link.click()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
      const status = response.headers["x-evidence-integrity"]
      if (status === "FAILED" || status === "MISSING") {
        toast.error("The stored original failed its integrity check. The downloaded file was not changed by this download.")
      } else {
        toast.success("Original evidence downloaded; stored-file integrity verified.")
      }
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setDownloading(false)
    }
  }

  if (!record) return <p className="text-sm text-slate-400">Loading evidence record…</p>

  return (
    <div>
      <PageHeader kicker={`EVD-${record.id}`} title={record.file_name} detail={record.description || "Digital evidence record"} />
      <div className="mb-6 flex flex-wrap gap-3">
        <Button variant="outline" disabled={downloading} onClick={() => void downloadOriginal()}>
          <Download /> {downloading ? "Downloading…" : "Download original"}
        </Button>
        <ActionButton icon={ShieldCheck} label="Verify" hint="Choose a file to compare against the reference hash" onClick={() => navigate(`/verify/${record.id}`)} tone="mint" />
        <ActionButton icon={FileSearch} label="View Metadata" hint="Review extracted file information" onClick={() => navigate(`/metadata/${record.id}`)} />
        <ActionButton icon={ScrollText} label="Audit" hint="Evidence audit trail" onClick={() => navigate(`/audit?evidenceId=${record.id}`)} />
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="glass-panel space-y-4 p-5">
          <div className="flex flex-wrap gap-2">
            <Badge>{record.status}</Badge>
            {integrity && (
              <Badge variant={integrity.verification_status === "VERIFIED" ? "default" : "danger"}>
                Stored original: {integrity.verification_status}
              </Badge>
            )}
            <Badge variant="muted">{record.file_type}</Badge>
            <Badge variant="muted">{formatBytes(record.file_size)}</Badge>
          </div>
          <div>
            <p className="mb-2 text-[10px] uppercase tracking-[0.2em] text-slate-500">SHA-256</p>
            <HashFingerprint hash={record.sha256_hash} />
          </div>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-slate-500">Case</dt>
              <dd>
                <Link className="text-ice hover:underline" to={`/cases/${record.case_id}`}>
                  {caseRecord?.case_number || `CASE-${record.case_id}`}
                </Link>
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Uploaded</dt>
              <dd>{formatDate(record.uploaded_at)}</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-slate-500">Storage path</dt>
              <dd className="break-all font-mono text-xs text-slate-400">{record.storage_path}</dd>
            </div>
          </dl>
        </div>
        <div className="glass-panel p-5">
          <h2 className="mb-4 text-sm uppercase tracking-[0.2em] text-slate-400">Recent Activity</h2>
          <CaseTimeline logs={logs} />
        </div>
      </div>
    </div>
  )
}
