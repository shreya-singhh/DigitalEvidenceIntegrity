import { FormEvent, useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"
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
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      await login(identity, password)
      toast.success("Session established")
      navigate("/dashboard")
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="command-grid relative flex min-h-screen flex-col items-center justify-center px-4 py-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent,rgba(5,7,12,0.88))]" />
      <form onSubmit={onSubmit} className="glass-panel relative z-10 w-full max-w-md p-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ice">Secure Login</p>
        <h1 className="mt-2 text-3xl font-semibold">Digital Evidence Integrity System</h1>
        <p className="mt-2 text-sm text-slate-400">Secure Digital Evidence Verification</p>
        <div className="relative z-10 mt-8 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="identity">Username or email</Label>
            <Input id="identity" value={identity} onChange={(e) => setIdentity(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <Button className="w-full" disabled={busy}>
            {busy ? "Signing in…" : "Login"}
          </Button>
        </div>
        <p className="relative z-10 mt-6 text-center text-sm text-slate-500">
          New user?{" "}
          <Link to="/register" className="text-ice hover:underline">
            Create an account
          </Link>
        </p>
        <p className="relative z-10 mt-5 text-center text-xs tracking-wide text-slate-400">
          Created &amp; Developed by Shreya Singh
        </p>
      </form>
      <CreatorFooter className="relative z-10 mt-6" />
    </div>
  )
}
