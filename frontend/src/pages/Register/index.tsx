import { FormEvent, useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Eye, EyeOff, Fingerprint } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CreatorFooter } from "@/components/layout/CreatorFooter"
import { useAuth } from "@/context/AuthContext"
import { authApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"

export default function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState("")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
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
    if (!termsAccepted) {
      toast.error("Accept the terms and privacy notice to continue")
      return
    }
    setBusy(true)
    try {
      await register({
        full_name: fullName.trim(),
        username: username.trim(),
        email: email.trim(),
        password,
        terms_accepted: termsAccepted,
      })
      try {
        const options = await authApi.options()
        if (options.data.email_delivery_enabled) {
          await authApi.requestEmailVerification()
          toast.success("Account created. Check your inbox to verify your email.")
        } else {
          toast.success("Account created. Email verification is not configured for this deployment.")
        }
      } catch (error) {
        toast.error(`Account created, but email verification could not be sent: ${extractApiError(error)}`)
      }
      navigate("/dashboard")
    } catch (error) {
      toast.error(extractApiError(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="command-grid relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4 py-8">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(8,145,178,0.13),transparent_48%),radial-gradient(circle_at_center,transparent,rgba(5,7,12,0.9))]" />
      <form onSubmit={onSubmit} className="glass-panel relative z-10 w-full max-w-lg p-6 sm:p-8">
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-ice/30 bg-ice/10 text-ice">
            <Fingerprint aria-hidden="true" className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-ice">DEIS // New Identity</p>
            <p className="mt-1 text-xs text-slate-400">Secure digital evidence workspace</p>
          </div>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Create your account</h1>
        <p className="mt-2 text-sm text-slate-400">Set up your identity to manage cases and evidence securely.</p>

        <div className="mt-7 grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="full-name">Full name</Label>
            <Input id="full-name" autoComplete="name" maxLength={120} value={fullName} onChange={(event) => setFullName(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="username">Unique username</Label>
            <Input id="username" autoComplete="username" minLength={3} maxLength={50} value={username} onChange={(event) => setUsername(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email address</Label>
            <Input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                minLength={12}
                maxLength={72}
                className="pr-11"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-slate-400 hover:text-ice"
                onClick={() => setShowPassword((value) => !value)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
              >
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm-password">Confirm password</Label>
            <div className="relative">
              <Input
                id="confirm-password"
                type={showConfirmation ? "text" : "password"}
                autoComplete="new-password"
                minLength={12}
                maxLength={72}
                className="pr-11"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                required
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-slate-400 hover:text-ice"
                onClick={() => setShowConfirmation((value) => !value)}
                aria-label={showConfirmation ? "Hide confirmation password" : "Show confirmation password"}
                aria-pressed={showConfirmation}
              >
                {showConfirmation ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </div>
          <p className="text-xs text-slate-500 sm:col-span-2">
            Use at least 12 characters with uppercase and lowercase letters, a number, and a symbol.
          </p>
          <label className="flex cursor-pointer items-start gap-2 text-sm leading-5 text-slate-400 sm:col-span-2">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(event) => setTermsAccepted(event.target.checked)}
              className="mt-1 h-4 w-4 rounded border-white/20 bg-slate-900 accent-cyan-400"
              required
            />
            <span>I accept the DEIS terms of use and privacy notice.</span>
          </label>
        </div>

        <Button className="mt-6 w-full" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </Button>
        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-ice hover:underline">Sign in</Link>
        </p>
      </form>
      <CreatorFooter className="relative z-10 mt-6" />
    </div>
  )
}
