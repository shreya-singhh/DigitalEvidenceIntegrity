import { useEffect, useMemo, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"
import { MetadataViewer } from "@/components/forensic/MetadataViewer"
import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { metadataApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"
import { useWorkspace } from "@/hooks/useWorkspace"
import type { MetadataPayload } from "@/types/api"

export default function MetadataPage() {
  const { evidenceId } = useParams()
  const { evidence, loading, error } = useWorkspace()
  const navigate = useNavigate()
  const [selected, setSelected] = useState(evidenceId || "")
  const [payload, setPayload] = useState<MetadataPayload | null>(null)
  const [busy, setBusy] = useState(false)
  const current = useMemo(() => evidence.find((e) => String(e.id) === selected), [evidence, selected])

  useEffect(() => {
    setSelected(evidenceId || "")
    setPayload(null)
    if (evidenceId) void load(evidenceId)
  }, [evidenceId])

  async function load(id: string) {
    setBusy(true)
    try {
      const res = await metadataApi.get(Number(id))
      setPayload(res.data)
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        kicker="Digital evidence"
        title="View Metadata"
        detail="Review information extracted from the selected evidence file."
      />
      <div className="mb-6 flex flex-wrap items-end gap-3">
        <div className="w-full max-w-lg">
          <Select
            value={selected}
            onValueChange={(value) => {
              setSelected(value)
              navigate(`/metadata/${value}`)
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder={loading ? "Loading evidence…" : "Select evidence"} />
            </SelectTrigger>
            <SelectContent>
              {evidence.map((item) => (
                <SelectItem key={item.id} value={String(item.id)}>
                  EVD-{item.id} · {item.file_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button disabled={!selected || busy} onClick={() => load(selected)}>
          {busy ? "Loading metadata…" : "View Metadata"}
        </Button>
      </div>
      {error && <p role="alert" className="mb-4 text-sm text-flare">Evidence list unavailable: {error}</p>}
      {current && <p className="mb-4 font-mono text-xs text-slate-500">{current.file_type} · {current.sha256_hash}</p>}
      {payload ? <MetadataViewer payload={payload} /> : <p className="text-sm text-slate-500">Select evidence to view its metadata.</p>}
    </div>
  )
}
