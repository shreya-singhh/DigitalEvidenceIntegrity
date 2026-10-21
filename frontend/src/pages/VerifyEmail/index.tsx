import { useState } from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { authApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"

export default function VerifyEmailPage() {
  const token = new URLSearchParams(window.location.hash.slice(1)).get("token") || ""
  const [statusText, setStatusText] = useState(token ? "" : "This verification link is incomplete.")
  const [busy, setBusy] = useState(false)

  async function verifyEmail() {
    setBusy(true)
    try {
      const { data } = await authApi.confirmEmailVerification(token)
      setStatusText(data.message)
    } catch (error) {
      setStatusText(extractApiError(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="command-grid relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-8">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(8,145,178,0.13),transparent_48%)]" />
      <section className="glass-panel relative z-10 w-full max-w-md p-6 text-center sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-ice">Contact verification</p>
        <h1 className="mt-3 text-3xl font-semibold">Email status</h1>
        {statusText && <p className="mt-4 text-sm text-slate-300" role="status">{statusText}</p>}
        {token && !statusText && (
          <Button className="mt-6" disabled={busy} onClick={verifyEmail}>
            {busy ? "Verifying…" : "Verify email address"}
          </Button>
        )}
        <Link to="/login" className="mt-6 inline-block text-sm text-ice hover:underline">Return to sign in</Link>
      </section>
    </main>
  )
}
