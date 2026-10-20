import { FormEvent, useEffect, useRef, useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Eye, EyeOff, Fingerprint, ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CreatorFooter } from "@/components/layout/CreatorFooter"
import { useAuth } from "@/context/AuthContext"
import { authApi } from "@/lib/api"
import { extractApiError } from "@/lib/utils"

type AuthOptions = {
  google_enabled: boolean
  google_client_id: string | null
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (options: {
            client_id: string
            callback: (response: { credential?: string }) => void
          }) => void
          renderButton: (element: HTMLElement, options: Record<string, string>) => void
        }
      }
    }
  }
}

export default function LoginPage() {
  const { user, login, loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const googleButton = useRef<HTMLDivElement>(null)
  const [identity, setIdentity] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(true)
  const [busy, setBusy] = useState(false)
  const [googleTermsAccepted, setGoogleTermsAccepted] = useState(false)
  const [options, setOptions] = useState<AuthOptions | null>(null)
  const [googleReady, setGoogleReady] = useState(false)

  useEffect(() => {
    authApi.options()
      .then(({ data }) => setOptions(data))
      .catch(() => setOptions({
        google_enabled: false,
        google_client_id: null,
      }))
  }, [])

  useEffect(() => {
    if (!options?.google_enabled || !options.google_client_id || !googleButton.current) return
    let script = document.querySelector<HTMLScriptElement>('script[src="https://accounts.google.com/gsi/client"]')
    const initialize = () => {
      if (!window.google || !googleButton.current) return
      window.google.accounts.id.initialize({
        client_id: options.google_client_id as string,
        callback: (response) => {
          if (!response.credential) {
            toast.error("Google sign-in did not return a credential")
            return
          }
          setBusy(true)
          loginWithGoogle(response.credential, googleTermsAccepted)
            .then(() => {
              toast.success("Signed in securely")
              navigate("/dashboard")
            })
            .catch((error) => toast.error(extractApiError(error)))
            .finally(() => setBusy(false))
        },
      })
      googleButton.current.replaceChildren()
      window.google.accounts.id.renderButton(googleButton.current, {
        theme: "filled_black",
        shape: "pill",
        size: "large",
        text: "signin_with",
        width: String(Math.min(360, googleButton.current.clientWidth)),
      })
      setGoogleReady(true)
    }
    if (!script) {
      script = document.createElement("script")
      script.src = "https://accounts.google.com/gsi/client"
      script.async = true
      script.defer = true
      script.onload = initialize
      script.onerror = () => setGoogleReady(false)
      document.head.appendChild(script)
    } else if (window.google) {
      initialize()
    } else {
      script.addEventListener("load", initialize, { once: true })
    }
    return () => {
      script?.removeEventListener("load", initialize)
    }
  }, [googleTermsAccepted, loginWithGoogle, navigate, options])

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
        <p className="mt-2 text-sm text-slate-400">Authenticate to access your evidence workspace.</p>

        <div className="mt-7 rounded-lg border border-white/10 bg-black/20 p-1" role="tablist" aria-label="Sign-in method">
          <button
            type="button"
            role="tab"
            aria-selected="true"
            className="w-full rounded-md bg-ice/15 px-3 py-2 text-sm text-ice"
          >
            Secure Access
          </button>
        </div>

        <div className="mt-6 space-y-4">
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

        {options?.google_enabled && (
          <div className="mt-6">
            <div className="mb-4 flex items-center gap-3 text-[10px] uppercase tracking-[0.18em] text-slate-500">
              <span className="h-px flex-1 bg-white/10" />
              or continue with
              <span className="h-px flex-1 bg-white/10" />
            </div>
            <label className="mb-3 flex cursor-pointer items-start gap-2 text-xs leading-5 text-slate-400">
              <input
                type="checkbox"
                checked={googleTermsAccepted}
                onChange={(event) => setGoogleTermsAccepted(event.target.checked)}
                className="mt-1 h-4 w-4 rounded border-white/20 bg-slate-900 accent-cyan-400"
              />
              <span>If this is a new DEIS account, I accept the terms of use and privacy notice.</span>
            </label>
            <div ref={googleButton} className="flex min-h-10 justify-center" aria-label="Sign in with Google" />
            {!googleReady && <p className="mt-2 text-center text-xs text-slate-500">Google sign-in is loading.</p>}
          </div>
        )}
        {options && !options.google_enabled && (
          <p className="mt-5 text-center text-xs text-slate-500">Google sign-in is not enabled for this deployment.</p>
        )}
        <div className="mt-7 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck aria-hidden="true" size={15} className="text-ice/70" />
          Protected with encrypted authentication
        </div>
        <p className="mt-5 text-center text-sm text-slate-500">
          New to DEIS?{" "}
          <Link to="/register" className="font-medium text-ice hover:underline">Create an account</Link>
        </p>
        <p className="mt-5 text-center text-xs tracking-wide text-slate-500">Created &amp; Developed by Shreya Singh</p>
      </form>
      <CreatorFooter className="relative z-10 mt-6" />
    </div>
  )
}
