import { FormEvent, useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CreatorFooter } from "@/components/layout/CreatorFooter"
import { useAuth } from "@/context/AuthContext"
import { extractApiError } from "@/lib/utils"

export default function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      await register(username, email, password)
      toast.success("Account created")
      navigate("/dashboard")
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="command-grid flex min-h-screen flex-col items-center justify-center px-4 py-8">
      <form onSubmit={onSubmit} className="glass-panel relative z-10 w-full max-w-md p-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ice">Digital Evidence Integrity System</p>
        <h1 className="mt-2 text-3xl font-semibold">Create account</h1>
        <div className="relative z-10 mt-8 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input id="username" minLength={3} value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password (8+)</Label>
            <Input id="password" type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <Button className="w-full" disabled={busy}>
            {busy ? "Creating account…" : "Create account"}
          </Button>
        </div>
        <p className="relative z-10 mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="text-ice hover:underline">
            Sign in
          </Link>
        </p>
      </form>
      <CreatorFooter className="mt-6" />
    </div>
  )
}
