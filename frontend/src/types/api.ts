export type User = {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
}

export type Token = {
  access_token: string
  token_type: string
}

export type CaseStatus = "OPEN" | "UNDER_REVIEW" | "CLOSED" | "ARCHIVED"
export type CasePriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"

export type CaseRecord = {
  id: number
  case_number: string
  title: string
  description: string | null
  status: CaseStatus
  priority: CasePriority
  created_by: number
  creator_username: string | null
  created_at: string
  updated_at: string
}

export type CaseCreate = {
  case_number: string
  title: string
  description?: string
  status?: CaseStatus
  priority?: CasePriority
}

export type CaseUpdate = {
  title?: string
  description?: string
  status?: CaseStatus
  priority?: CasePriority
}

export type EvidenceRecord = {
  id: number
  case_id: number
  owner_id: number
  file_name: string
  file_type: string
  file_size: number
  storage_path: string
  sha256_hash: string
  description: string | null
  status: string
  uploaded_at: string
  updated_at: string
}

export type VerificationStatus = "VERIFIED" | "FAILED" | "MISSING"

export type VerificationResult = {
  evidence_id: number
  verification_status: VerificationStatus
  stored_hash: string
  current_hash: string | null
  verified_at: string | null
  message: string
}

export type ChainOfCustodyEvent = {
  id: number
  evidence_id: number
  user_id: number
  username: string
  action: string
  description: string | null
  timestamp: string
}

export type EvidenceCustody = {
  evidence_id: number
  file_name: string
  case_id: number
  case_number: string
  reference_hash: string
  events: ChainOfCustodyEvent[]
}

export type AuditLog = {
  id: number
  user_id: number | null
  case_id: number | null
  evidence_id: number | null
  action: string
  entity_type: string | null
  entity_id: number | null
  description: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export type MetadataPayload = {
  file_type: string
  mime_type: string | null
  metadata: Record<string, unknown>
  extraction_status: string
  extraction_errors: string[]
}

export type HealthResponse = {
  status: string
  version: string
}

export type DashboardSummary = {
  active_cases: number
  total_evidence: number
  verified_evidence: number
  integrity_failed_evidence: number
  pending_verification: number
  verification_records: number
  audit_events: number
}
