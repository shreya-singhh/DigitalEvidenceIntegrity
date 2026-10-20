import { FormEvent, useState } from "react"
import { Link } from "react-router-dom"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { authApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"

export default function ResetPasswordPage() {
  const token = new URLSearchParams(window.location.hash.slice(1)).get("token") || ""
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [busy, setBusy] = useState(false)
  const [complete, setComplete] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!token) {
      toast.error("This reset link is invalid or incomplete")
      return
    }
    if (password !== confirmPassword) {
      toast.error("Passwords do not match")
      return
    }
    if (
      password.length < 12 ||
      new TextEncoder().encode(password).length > 72 ||
      !/[a-z]/.test(password) ||
      !/[A-Z]/.test(password) ||
      !/[0-9]/.test(password) ||
      !/[^A-Za-z0-9]/.test(password)
    ) {
      toast.error("Use 12 or more characters with uppercase, lowercase, a number, and a symbol")
      return
    }
    setBusy(true)
    try {
      const { data } = await authApi.confirmPasswordReset(token, password)
      setComplete(true)
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
        <h1 className="mt-3 text-3xl font-semibold">Choose a new password</h1>
        {complete ? (
          <p className="mt-5 text-sm text-slate-300">Your password has been updated. <Link to="/login" className="text-ice hover:underline">Sign in</Link></p>
        ) : !token ? (
          <p className="mt-5 text-sm text-slate-400">This reset link is missing its token or has expired. <Link to="/forgot-password" className="text-ice hover:underline">Request another</Link>.</p>
        ) : (
          <form onSubmit={onSubmit} className="mt-7 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="password">New password</Label>
              <Input id="password" type="password" autoComplete="new-password" minLength={12} maxLength={72} value={password} onChange={(event) => setPassword(event.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm new password</Label>
              <Input id="confirm-password" type="password" autoComplete="new-password" minLength={12} maxLength={72} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
            </div>
            <p className="text-xs text-slate-500">At least 12 characters with uppercase and lowercase letters, a number, and a symbol.</p>
            <Button className="w-full" disabled={busy}>{busy ? "Updating…" : "Update password"}</Button>
          </form>
        )}
      </section>
    </main>
  )
}
