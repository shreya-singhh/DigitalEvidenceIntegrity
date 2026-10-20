import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import { authApi, healthApi } from "@/lib/api"
import { extractApiError, formatDate } from "@/lib/utils"

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [health, setHealth] = useState<string>("checking")

  useEffect(() => {
    healthApi
      .ping()
      .then((res) => setHealth(`${res.data.status} · v${res.data.version}`))
      .catch((err) => setHealth(extractApiError(err)))
  }, [])

  async function requestEmailVerification() {
    try {
      const { data } = await authApi.requestEmailVerification()
      toast.success(data.message)
    } catch (error) {
      toast.error(extractApiError(error))
    }
  }

  return (
    <div>
      <PageHeader kicker="Account and system" title="Settings" detail="View account details and check the backend connection." />
      <div className="grid gap-4 md:grid-cols-2">
        <div className="glass-panel p-5">
          <h2 className="text-sm uppercase tracking-[0.2em] text-slate-400">Identity</h2>
          <dl className="relative z-10 mt-4 space-y-3 text-sm">
            <div>
              <dt className="text-slate-500">Username</dt>
              <dd>{user?.username}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Email</dt>
              <dd>{user?.email} <span className="text-xs text-slate-500">{user?.email_verified ? "· verified" : "· unverified"}</span></dd>
            </div>
            <div>
              <dt className="text-slate-500">Status</dt>
              <dd>{user?.is_active ? "Active" : "Disabled"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Enrolled</dt>
              <dd>{formatDate(user?.created_at)}</dd>
            </div>
          </dl>
          {user && !user.email_verified && (
            <Button className="relative z-10 mt-4" variant="outline" size="sm" onClick={requestEmailVerification}>
              Send email verification
            </Button>
          )}
          <Button
            className="relative z-10 mt-6"
            variant="danger"
            onClick={() => void logout().then(() => {
              toast.message("Session ended")
              navigate("/login")
            })}
          >
            End session
          </Button>
        </div>
        <div className="glass-panel p-5">
          <h2 className="text-sm uppercase tracking-[0.2em] text-slate-400">Backend Status</h2>
          <p className="relative z-10 mt-4 font-mono text-ice">{health}</p>
          <p className="relative z-10 mt-3 text-sm text-slate-400">
            API traffic is proxied through Vite to FastAPI (`/api`). The bearer token is stored in browser storage according to the sign-in persistence choice.
          </p>
          <p className="relative z-10 mt-3 text-xs text-slate-500">
            Supported file types: PDF, JPG, JPEG, PNG, MP4, MP3, DOCX, and TXT · 25 MB maximum.
          </p>
        </div>
        <section className="glass-panel p-5 md:col-span-2" aria-labelledby="creator-about-heading">
          <h2 id="creator-about-heading" className="text-sm uppercase tracking-[0.2em] text-slate-400">
            About the Creator
          </h2>
          <p className="relative z-10 mt-4 text-lg font-medium text-slate-200">Shreya Singh</p>
          <p className="relative z-10 mt-1 text-sm text-slate-400">
            Creator and developer of the Digital Evidence Integrity System.
          </p>
        </section>
      </div>
    </div>
  )
}
