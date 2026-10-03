import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { toast } from "sonner"
import { IntegrityStatus } from "@/components/forensic/IntegrityStatus"
import { TamperResult } from "@/components/forensic/TamperResult"
import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { evidenceApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"
import { useWorkspace } from "@/hooks/useWorkspace"
import type { VerificationResult } from "@/types/api"

export default function VerifyPage() {
  const { evidenceId } = useParams()
  const { evidence, loading, error } = useWorkspace()
  const [selected, setSelected] = useState(evidenceId || "")
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<VerificationResult | null>(null)
  const [file, setFile] = useState<File | null>(null)

  useEffect(() => {
    setSelected(evidenceId || "")
    setResult(null)
    setFile(null)
  }, [evidenceId])

  const selectedEvidence = evidence.find((item) => String(item.id) === selected)

  async function run() {
    if (!selected || !file) return
    setBusy(true)
    setResult(null)
    try {
      const res = await evidenceApi.verify(Number(selected), file)
      setResult(res.data)
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        kicker="SHA-256 comparison"
        title="Verify Integrity"
        detail="Select a registered evidence record and the file to verify. The submitted file is hashed and compared with its immutable reference SHA-256."
      />
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <div className="glass-panel p-4">
          <IntegrityStatus status={result?.verification_status ?? "IDLE"} />
        </div>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <div className="min-w-72 flex-1">
              <Select
                value={selected}
                onValueChange={(value) => {
                  setSelected(value)
                  setResult(null)
                  setFile(null)
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
          </div>
          {selectedEvidence && (
            <div className="glass-panel space-y-2 p-4">
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-400">
                Original / Reference SHA-256 · EVD-{selectedEvidence.id}
              </p>
              <p className="break-all font-mono text-xs text-ice">{selectedEvidence.sha256_hash}</p>
            </div>
          )}
          <div className="glass-panel space-y-3 p-4">
            <Label htmlFor="verification-file">File to Verify</Label>
            <Input
              key={selected || "no-evidence"}
              id="verification-file"
              type="file"
              disabled={!selected || busy}
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null)
                setResult(null)
              }}
            />
            <p className="text-xs text-slate-400">
              {file ? `Selected: ${file.name}` : "Choose the original file or a copy to compare against the registered reference."}
            </p>
          </div>
          <Button disabled={!selected || !file || busy} onClick={run}>
            {busy ? "Comparing submitted file…" : "Verify Integrity"}
          </Button>
          {error && <p role="alert" className="text-sm text-flare">Evidence list unavailable: {error}</p>}
          {result && <TamperResult result={result} />}
        </div>
      </div>
    </div>
  )
}
