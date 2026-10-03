import { FormEvent, useMemo, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { toast } from "sonner"
import { DropZone } from "@/components/forensic/DropZone"
import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { HashFingerprint } from "@/components/forensic/HashFingerprint"
import { evidenceApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"
import { useWorkspace } from "@/hooks/useWorkspace"
import type { EvidenceRecord } from "@/types/api"

export default function UploadPage() {
  const { cases, loading, error, reload } = useWorkspace()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const preset = params.get("caseId")
  const [caseId, setCaseId] = useState(preset || "")
  const [description, setDescription] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [scanning, setScanning] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const [result, setResult] = useState<EvidenceRecord | null>(null)

  const selectedCase = useMemo(() => cases.find((c) => String(c.id) === caseId), [cases, caseId])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!file || !caseId) {
      toast.error("Select a case and a file")
      return
    }
    const form = new FormData()
    form.append("case_id", caseId)
    if (description) form.append("description", description)
    form.append("file", file)
    setScanning(true)
    setUploadProgress(0)
    setResult(null)
    try {
      const res = await evidenceApi.upload(form, setUploadProgress)
      setResult(res.data)
      setUploadProgress(100)
      toast.success("Evidence uploaded")
      await reload()
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setScanning(false)
    }
  }

  return (
    <div>
      <PageHeader
        kicker="Digital evidence"
        title="Upload Evidence"
        detail="POST /api/evidence/upload stores the file, computes SHA-256, and writes an audit event."
      />
      <form onSubmit={onSubmit} className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          <DropZone onFile={setFile} scanning={scanning} fileName={file?.name} />
          {scanning && (
            <div className="glass-panel p-4" aria-live="polite">
              <div className="mb-2 flex items-center justify-between text-xs text-slate-300">
                <span>{uploadProgress === 100 ? "File received; calculating SHA-256…" : "Uploading evidence…"}</span>
                <span>{uploadProgress ?? 0}%</span>
              </div>
              <progress className="h-2 w-full accent-cyan-300" value={uploadProgress ?? 0} max={100} aria-label="Evidence upload progress" />
            </div>
          )}
          {result && (
            <div className="glass-panel p-5">
              <p className="text-sm text-mint">Upload complete · EVD-{result.id}</p>
              <HashFingerprint className="mt-3" hash={result.sha256_hash} />
              <Button type="button" className="mt-4" variant="outline" onClick={() => navigate(`/evidence/${result.id}`)}>
                Open evidence record
              </Button>
            </div>
          )}
        </div>
        <div className="glass-panel space-y-4 p-5">
          <div className="space-y-2">
            <Label>Target case</Label>
            <Select value={caseId} onValueChange={setCaseId} disabled={loading || cases.length === 0}>
              <SelectTrigger>
                <SelectValue placeholder={loading ? "Loading cases…" : "Select case"} />
              </SelectTrigger>
              <SelectContent>
                {cases.map((item) => (
                  <SelectItem key={item.id} value={String(item.id)}>
                    {item.case_number} — {item.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {error && <p role="alert" className="text-xs text-flare">Could not load cases: {error}</p>}
            {!loading && !error && !cases.length && (
              <p className="text-xs text-slate-500">Open a case before uploading evidence.</p>
            )}
            {selectedCase && <p className="text-xs text-slate-500">{selectedCase.status} · {selectedCase.priority}</p>}
          </div>
          <div className="space-y-2">
            <Label>Description</Label>
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Add relevant details about this evidence…" />
          </div>
          <Button className="w-full" disabled={scanning || loading || !cases.length || !caseId || !file}>
            {scanning ? "Calculating SHA-256 hash…" : "Upload Evidence"}
          </Button>
        </div>
      </form>
    </div>
  )
}
