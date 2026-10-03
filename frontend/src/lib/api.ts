import axios from "axios"
import type {
  AuditLog,
  CaseCreate,
  CaseRecord,
  CaseUpdate,
  EvidenceCustody,
  DashboardSummary,
  EvidenceRecord,
  HealthResponse,
  MetadataPayload,
  Token,
  User,
  VerificationResult,
} from "@/types/api"

const TOKEN_KEY = "deis.access_token"

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
})

api.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"]
  }
  return config
})

export const authApi = {
  login: (payload: { username?: string; email?: string; password: string }) =>
    api.post<Token>("/auth/login", payload),
  register: (payload: { username: string; email: string; password: string }) =>
    api.post<User>("/auth/register", payload),
  me: () => api.get<User>("/auth/me"),
}

export const casesApi = {
  list: () => api.get<CaseRecord[]>("/cases"),
  get: (id: number) => api.get<CaseRecord>(`/cases/${id}`),
  create: (payload: CaseCreate) => api.post<CaseRecord>("/cases", payload),
  update: (id: number, payload: CaseUpdate) => api.patch<CaseRecord>(`/cases/${id}`, payload),
}

export const evidenceApi = {
  list: () => api.get<EvidenceRecord[]>("/evidence"),
  upload: (form: FormData, onUploadProgress?: (percent: number) => void) =>
    api.post<EvidenceRecord>("/evidence/upload", form, {
      onUploadProgress: (event) => {
        if (event.total) onUploadProgress?.(Math.round((event.loaded * 100) / event.total))
      },
    }),
  get: (id: number) => api.get<EvidenceRecord>(`/evidence/${id}`),
  listByCase: (caseId: number) => api.get<EvidenceRecord[]>(`/evidence/cases/${caseId}`),
  verify: (id: number, file: File) => {
    const form = new FormData()
    form.append("file", file)
    return api.post<VerificationResult>(`/evidence/${id}/verify`, form)
  },
}

export const chainOfCustodyApi = {
  getForEvidence: (evidenceId: number) =>
    api.get<EvidenceCustody>(`/chain-of-custody/evidence/${evidenceId}`),
}

export const metadataApi = {
  get: (evidenceId: number) => api.get<MetadataPayload>(`/metadata/evidence/${evidenceId}`),
}

export const auditApi = {
  list: (skip = 0, limit = 50) => api.get<AuditLog[]>("/audit", { params: { skip, limit } }),
  byCase: (caseId: number, skip = 0, limit = 50) =>
    api.get<AuditLog[]>(`/audit/case/${caseId}`, { params: { skip, limit } }),
  byEvidence: (evidenceId: number, skip = 0, limit = 50) =>
    api.get<AuditLog[]>(`/audit/evidence/${evidenceId}`, { params: { skip, limit } }),
  get: (id: number) => api.get<AuditLog>(`/audit/${id}`),
}

export const healthApi = {
  ping: () => api.get<HealthResponse>("/health"),
}

export const dashboardApi = {
  summary: () => api.get<DashboardSummary>("/dashboard"),
}

export const reportsApi = {
  case: (caseId: number) =>
    api.get<Blob>(`/reports/case/${caseId}`, { responseType: "blob" }),
}
