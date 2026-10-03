import { FormEvent, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { toast } from "sonner"
import { PageHeader } from "@/components/layout/PageHeader"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { casesApi } from "@/lib/api"
import { extractApiError, formatDate } from "@/lib/utils"
import type { CasePriority, CaseRecord, CaseStatus } from "@/types/api"
import { useWorkspace } from "@/hooks/useWorkspace"

const priorityTone: Record<CasePriority, "muted" | "default" | "warn" | "danger"> = {
  LOW: "muted",
  MEDIUM: "default",
  HIGH: "warn",
  CRITICAL: "danger",
}

export default function CasesPage() {
  const { cases, evidence, loading, error, reload } = useWorkspace()
  const [open, setOpen] = useState(false)
  const counts = useMemo(() => {
    const map = new Map<number, number>()
    evidence.forEach((item) => map.set(item.case_id, (map.get(item.case_id) || 0) + 1))
    return map
  }, [evidence])

  return (
    <div>
      <div className="mb-6 flex items-end justify-between gap-4">
        <PageHeader kicker="Case records" title="Cases" detail="Cases are associated with the logged-in user." />
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Open case</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New case</DialogTitle>
            </DialogHeader>
            <CaseForm
              onCreated={async () => {
                setOpen(false)
                await reload()
              }}
            />
          </DialogContent>
        </Dialog>
      </div>
      {loading ? (
        <p className="text-sm text-slate-400">Loading cases…</p>
      ) : error ? (
        <div role="alert" className="glass-panel flex flex-wrap items-center justify-between gap-3 border-flare/30 p-5">
          <p className="text-sm text-flare">Cases could not be loaded: {error}</p>
          <button type="button" onClick={() => void reload()} className="text-xs uppercase tracking-wider text-ice hover:underline">
            Retry
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {cases.map((item) => (
            <Link key={item.id} to={`/cases/${item.id}`} className="glass-panel block p-5 hover:border-ice/40">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-mono text-xs text-ice">{item.case_number}</p>
                  <h2 className="mt-1 text-xl">{item.title}</h2>
                </div>
                <Badge variant={priorityTone[item.priority]}>{item.priority}</Badge>
              </div>
              <p className="mt-3 line-clamp-2 text-sm text-slate-400">{item.description || "No synopsis"}</p>
              <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
                <Badge variant="muted">{item.status.replace("_", " ")}</Badge>
                <span>
                  {counts.get(item.id) || 0} evidence records · Created {formatDate(item.created_at)}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-500">Created by {item.creator_username || `User ${item.created_by}`}</p>
            </Link>
          ))}
          {!cases.length && <p className="text-sm text-slate-500">No cases have been created yet.</p>}
        </div>
      )}
    </div>
  )
}

function CaseForm({ onCreated, existing }: { onCreated: () => Promise<void>; existing?: CaseRecord }) {
  const [caseNumber, setCaseNumber] = useState(existing?.case_number || "")
  const [title, setTitle] = useState(existing?.title || "")
  const [description, setDescription] = useState(existing?.description || "")
  const [status, setStatus] = useState<CaseStatus>(existing?.status || "OPEN")
  const [priority, setPriority] = useState<CasePriority>(existing?.priority || "MEDIUM")
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      if (existing) {
        await casesApi.update(existing.id, { title, description, status, priority })
        toast.success("Case updated")
      } else {
        await casesApi.create({ case_number: caseNumber, title, description, status, priority })
        toast.success("Case opened")
      }
      await onCreated()
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {!existing && (
        <div className="space-y-2">
          <Label>Case number</Label>
          <Input value={caseNumber} onChange={(e) => setCaseNumber(e.target.value)} minLength={3} required />
        </div>
      )}
      <div className="space-y-2">
        <Label>Title</Label>
        <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label>Synopsis</Label>
        <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>Status</Label>
          <Select value={status} onValueChange={(v) => setStatus(v as CaseStatus)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {["OPEN", "UNDER_REVIEW", "CLOSED", "ARCHIVED"].map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Priority</Label>
          <Select value={priority} onValueChange={(v) => setPriority(v as CasePriority)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <Button className="w-full" disabled={busy}>
        {busy ? "Saving…" : existing ? "Update case" : "Create case"}
      </Button>
    </form>
  )
}

export { CaseForm }
