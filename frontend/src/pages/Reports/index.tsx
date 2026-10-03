import { useState } from "react"
import { Link } from "react-router-dom"
import axios from "axios"
import { toast } from "sonner"
import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useWorkspace } from "@/hooks/useWorkspace"
import { extractApiError, formatDate } from "@/lib/utils"
import { reportsApi } from "@/lib/api"

export default function ReportsPage() {
  const { cases, loading, error, reload } = useWorkspace()
  const [caseId, setCaseId] = useState("")
  const [generating, setGenerating] = useState(false)

  async function download() {
    if (!caseId) return
    setGenerating(true)
    try {
      const response = await reportsApi.case(Number(caseId))
      const url = URL.createObjectURL(response.data)
      const anchor = document.createElement("a")
      anchor.href = url
      const filename = response.headers["content-disposition"]?.match(/filename="?([^";]+)"?/)?.[1]
      anchor.download = filename || `case-${caseId}-integrity-report.json`
      document.body.append(anchor)
      anchor.click()
      anchor.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
      toast.success("Case integrity report generated")
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data instanceof Blob) {
        const body = await err.response.data.text()
        try {
          const parsed = JSON.parse(body) as { detail?: string }
          toast.error(parsed.detail || body || "Report generation failed")
        } catch {
          toast.error(body || "Report generation failed")
        }
      } else {
        toast.error(extractApiError(err))
      }
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div>
      <PageHeader
        kicker="Forensic documentation"
        title="Reports"
        detail="Generate a server-side case integrity report with evidence inventory, stored SHA-256 values, and a fresh integrity comparison for each file."
      />
      {loading ? (
        <p className="text-sm text-slate-400">Loading case records…</p>
      ) : error ? (
        <div role="alert" className="glass-panel flex flex-wrap items-center justify-between gap-3 border-flare/30 p-5">
          <p className="text-sm text-flare">Case records could not be loaded: {error}</p>
          <Button variant="outline" onClick={() => void reload()}>Retry</Button>
        </div>
      ) : (
        <div className="glass-panel max-w-2xl space-y-5 p-6">
          {cases.length ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="report-case">Case record</Label>
                <Select value={caseId} onValueChange={setCaseId}>
                  <SelectTrigger id="report-case">
                    <SelectValue placeholder="Select a case" />
                  </SelectTrigger>
                  <SelectContent>
                    {cases.map((item) => (
                      <SelectItem key={item.id} value={String(item.id)}>
                        {item.case_number} — {item.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={() => void download()} disabled={!caseId || generating}>
                {generating ? "Generating report…" : "Generate and download"}
              </Button>
              <p className="text-xs text-slate-500">Reports include current server-side hash comparisons and are recorded in the audit trail.</p>
            </>
          ) : (
            <div className="space-y-2 text-sm text-slate-400">
              <p>No case records are available for report generation.</p>
              <Link to="/cases" className="text-ice hover:underline">Create a case first</Link>
            </div>
          )}
          {caseId && (
            <p className="text-xs text-slate-500">
              Selected case created {formatDate(cases.find((item) => String(item.id) === caseId)?.created_at)}.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
