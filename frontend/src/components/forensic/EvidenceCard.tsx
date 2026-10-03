import { Link } from "react-router-dom"
import { FileDigit, ShieldCheck } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { HashFingerprint } from "@/components/forensic/HashFingerprint"
import { formatBytes, formatDate } from "@/lib/utils"
import type { EvidenceRecord } from "@/types/api"

export function EvidenceCard({ evidence, caseNumber }: { evidence: EvidenceRecord; caseNumber?: string }) {
  return (
    <Link
      to={`/evidence/${evidence.id}`}
      className="glass-panel group block p-5 transition hover:-translate-y-0.5 hover:border-ice/40"
    >
      <div className="relative z-10 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md border border-ice/20 bg-ice/10 text-ice">
            <FileDigit className="h-5 w-5" />
          </div>
          <div>
            <p className="font-medium text-slate-100">{evidence.file_name}</p>
            <p className="text-xs text-slate-500">
              {caseNumber ? `${caseNumber} · ` : ""}EVD-{evidence.id} · {formatBytes(evidence.file_size)}
            </p>
          </div>
        </div>
        <Badge variant={evidence.status.toLowerCase().includes("fail") ? "danger" : "success"}>
          {evidence.status}
        </Badge>
      </div>
      <div className="relative z-10 mt-4">
        <p className="mb-2 text-[10px] uppercase tracking-[0.2em] text-slate-500">SHA-256 fingerprint</p>
        <HashFingerprint hash={evidence.sha256_hash} />
      </div>
      <div className="relative z-10 mt-4 flex items-center justify-between text-xs text-slate-500">
        <span className="inline-flex items-center gap-1">
          <ShieldCheck className="h-3.5 w-3.5 text-ice" />
          {evidence.file_type}
        </span>
        <span>{formatDate(evidence.uploaded_at)}</span>
      </div>
    </Link>
  )
}
