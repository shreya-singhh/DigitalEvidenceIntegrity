import { Link } from "react-router-dom"
import { formatDate } from "@/lib/utils"
import type { AuditLog } from "@/types/api"

export function CaseTimeline({ logs }: { logs: AuditLog[] }) {
  if (!logs.length) {
    return <p className="text-sm text-slate-500">No activity has been recorded yet.</p>
  }

  return (
    <ol className="relative space-y-5 border-l border-ice/20 pl-6">
      {logs.map((log) => (
        <li key={log.id} className="relative">
          <span className="absolute -left-[29px] top-1 h-3 w-3 rounded-full border border-ice bg-[#071018] shadow-glow" />
          <p className="text-[10px] uppercase tracking-[0.2em] text-ice">{log.action}</p>
          <p className="text-sm text-slate-200">{log.description || "Event recorded"}</p>
          <p className="mt-1 text-xs text-slate-500">
            {formatDate(log.created_at)}
            {log.evidence_id ? (
              <>
                {" · "}
                <Link className="text-ice hover:underline" to={`/evidence/${log.evidence_id}`}>
                  EVD-{log.evidence_id}
                </Link>
              </>
            ) : null}
            {log.case_id ? ` · CASE-${log.case_id}` : ""}
          </p>
        </li>
      ))}
    </ol>
  )
}
