import { useEffect, useState, type FormEvent } from "react"
import { Link, useParams } from "react-router-dom"
import { toast } from "sonner"
import { useAuth } from "@/context/AuthContext"
import { CaseTimeline } from "@/components/forensic/CaseTimeline"
import { EvidenceCard } from "@/components/forensic/EvidenceCard"
import { PageHeader } from "@/components/layout/PageHeader"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CaseForm } from "@/pages/Cases"
import { auditApi, casesApi, evidenceApi } from "@/lib/api"
import { extractApiError, formatDate } from "@/lib/utils"
import type { AuditLog, CaseAccessGrant, CaseRecord, EvidenceRecord } from "@/types/api"

export default function CaseDetailPage() {
  const { caseId } = useParams()
  const id = Number(caseId)
  const { user } = useAuth()
  const [record, setRecord] = useState<CaseRecord | null>(null)
  const [items, setItems] = useState<EvidenceRecord[]>([])
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [grants, setGrants] = useState<CaseAccessGrant[]>([])
  const [shareEmail, setShareEmail] = useState("")
  const [sharing, setSharing] = useState(false)
  const [open, setOpen] = useState(false)
  const isOwner = record?.created_by === user?.id

  async function load() {
    try {
      const [caseRes, evRes, logRes] = await Promise.all([
        casesApi.get(id),
        evidenceApi.listByCase(id),
        auditApi.byCase(id, 0, 100),
      ])
      setRecord(caseRes.data)
      setItems(evRes.data)
      setLogs(logRes.data)
      if (caseRes.data.created_by === user?.id) {
        const accessRes = await casesApi.access(id)
        setGrants(accessRes.data)
      } else {
        setGrants([])
      }
    } catch (err) {
      toast.error(extractApiError(err))
    }
  }

  useEffect(() => {
    if (Number.isFinite(id)) void load()
  }, [id, user?.id])

  async function grantAccess(event: FormEvent) {
    event.preventDefault()
    setSharing(true)
    try {
      await casesApi.grantAccess(id, shareEmail)
      setShareEmail("")
      toast.success("Case access granted")
      await load()
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setSharing(false)
    }
  }

  async function revokeAccess(userId: number) {
    try {
      await casesApi.revokeAccess(id, userId)
      toast.success("Case access revoked")
      await load()
    } catch (err) {
      toast.error(extractApiError(err))
    }
  }

  if (!record) return <p className="text-sm text-slate-400">Loading case…</p>

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <PageHeader kicker={record.case_number} title={record.title} detail={record.description || undefined} />
        <div className="flex gap-2">
          {isOwner && (
            <>
              <Button asChild variant="outline">
                <Link to={`/upload?caseId=${record.id}`}>Upload evidence</Link>
              </Button>
              <Dialog open={open} onOpenChange={setOpen}>
                <DialogTrigger asChild>
                  <Button variant="ghost">Amend</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Update case</DialogTitle>
                  </DialogHeader>
                  <CaseForm
                    existing={record}
                    onCreated={async () => {
                      setOpen(false)
                      await load()
                    }}
                  />
                </DialogContent>
              </Dialog>
            </>
          )}
        </div>
      </div>
      <div className="mb-6 flex gap-2">
        <Badge>{record.status}</Badge>
        <Badge variant="warn">{record.priority}</Badge>
        <span className="text-xs text-slate-500">Updated {formatDate(record.updated_at)}</span>
      </div>
      <dl className="mb-6 grid gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-slate-500">Created</dt>
          <dd>{formatDate(record.created_at)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Created by</dt>
          <dd>{record.creator_username || `User ${record.created_by}`}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Evidence records</dt>
          <dd>{items.length}</dd>
        </div>
      </dl>
      {isOwner && (
        <section className="mb-6 glass-panel p-5">
          <h2 className="mb-1 text-sm uppercase tracking-[0.2em] text-slate-300">Investigator access</h2>
          <p className="mb-4 text-sm text-slate-500">Grant evidence access to an active registered user by email.</p>
          <form onSubmit={(event) => void grantAccess(event)} className="flex flex-wrap items-end gap-3">
            <div className="min-w-64 flex-1 space-y-2">
              <Label htmlFor="investigator-email">Investigator email</Label>
              <Input
                id="investigator-email"
                type="email"
                autoComplete="email"
                required
                value={shareEmail}
                onChange={(event) => setShareEmail(event.target.value)}
              />
            </div>
            <Button type="submit" disabled={sharing}>{sharing ? "Granting…" : "Grant access"}</Button>
          </form>
          <ul className="mt-4 divide-y divide-white/10">
            {grants.map((grant) => (
              <li key={grant.user_id} className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
                <span>{grant.username} <span className="text-slate-500">({grant.email})</span></span>
                <Button type="button" variant="danger" size="sm" onClick={() => void revokeAccess(grant.user_id)}>
                  Revoke
                </Button>
              </li>
            ))}
            {!grants.length && <li className="pt-3 text-sm text-slate-500">No investigators have access.</li>}
          </ul>
        </section>
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          {items.map((item) => (
            <EvidenceCard key={item.id} evidence={item} caseNumber={record.case_number} />
          ))}
          {!items.length && <p className="text-sm text-slate-500">No evidence attached.</p>}
        </div>
        <div className="glass-panel p-5">
          <h2 className="mb-4 text-sm uppercase tracking-[0.2em] text-slate-400">Activity timeline</h2>
          <CaseTimeline logs={logs} />
        </div>
      </div>
    </div>
  )
}
