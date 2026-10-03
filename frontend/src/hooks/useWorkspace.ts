import { useCallback, useEffect, useState } from "react"
import { auditApi, casesApi, evidenceApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"
import type { AuditLog, CaseRecord, EvidenceRecord } from "@/types/api"

export function useWorkspace() {
  const [cases, setCases] = useState<CaseRecord[]>([])
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([])
  const [audit, setAudit] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [caseRes, auditRes] = await Promise.all([casesApi.list(), auditApi.list(0, 100)])
      const caseList = caseRes.data
      const evidenceRes = await evidenceApi.list()
      setCases(caseList)
      setEvidence(evidenceRes.data)
      setAudit(auditRes.data)
    } catch (err) {
      setError(extractApiError(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void reload()
  }, [reload])

  return { cases, evidence, audit, loading, error, reload }
}
