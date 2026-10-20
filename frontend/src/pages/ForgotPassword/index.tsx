import { FormEvent, useState } from "react"
import { Link } from "react-router-dom"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { authApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [busy, setBusy] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    try {
      const { data } = await authApi.requestPasswordReset(email.trim())
      setSubmitted(true)
      toast.success(data.message)
    } catch (error) {
      toast.error(extractApiError(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="command-grid relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-8">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(8,145,178,0.13),transparent_48%)]" />
      <section className="glass-panel relative z-10 w-full max-w-md p-6 sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-ice">Account recovery</p>
        <h1 className="mt-3 text-3xl font-semibold">Reset your password</h1>
        <p className="mt-2 text-sm text-slate-400">
          Enter the email address associated with your account. If an account matches, reset instructions will be sent.
        </p>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email address</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>
          <Button className="w-full" disabled={busy || submitted}>
            {busy ? "Please wait…" : submitted ? "Request complete" : "Send reset instructions"}
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-500">
          Remember your password? <Link to="/login" className="text-ice hover:underline">Back to sign in</Link>
        </p>
      </section>
    </main>
  )
}
