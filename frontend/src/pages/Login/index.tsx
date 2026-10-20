import { FormEvent, useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Eye, EyeOff, Fingerprint } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CreatorFooter } from "@/components/layout/CreatorFooter"
import { useAuth } from "@/context/AuthContext"
import { extractApiError } from "@/lib/utils"

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [identity, setIdentity] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(true)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    try {
      await login(identity.trim(), password, remember)
      toast.success("Signed in securely")
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
      <form onSubmit={onSubmit} className="glass-panel relative z-10 w-full max-w-md p-6 sm:p-8">
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-ice/30 bg-ice/10 text-ice">
            <Fingerprint aria-hidden="true" className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-ice">DEIS // Secure Access</p>
            <p className="mt-1 text-xs text-slate-400">Digital Evidence Integrity System</p>
          </div>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Welcome back</h1>
        <p className="mt-2 text-sm text-slate-400">Sign in with your DEIS username or email and password.</p>

        <div className="mt-7 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="identity">Username or email</Label>
            <Input
              id="identity"
              name="username"
              autoComplete="username"
              value={identity}
              onChange={(event) => setIdentity(event.target.value)}
              placeholder="Enter your username or email"
              required
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              <Link to="/forgot-password" className="text-xs text-ice hover:underline">Forgot password?</Link>
            </div>
            <div className="relative">
              <Input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
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
          <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={remember}
              onChange={(event) => setRemember(event.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-slate-900 accent-cyan-400"
            />
            Keep me signed in on this device
          </label>
          <Button className="w-full" disabled={busy}>
            {busy ? "Please wait…" : "Sign in"}
          </Button>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          Need an account?{" "}
          <Link to="/register" className="font-medium text-ice hover:underline">Create one</Link>
        </p>
      </form>
      <CreatorFooter className="relative z-10 mt-6" />
    </div>
  )
}
