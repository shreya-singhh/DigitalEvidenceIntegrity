import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { toast } from "sonner"
import { authApi, getStoredToken, setStoredToken } from "@/lib/api"
import { extractApiError } from "@/lib/utils"
import type { User } from "@/types/api"

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (identity: string, password: string, remember?: boolean) => Promise<void>
  loginWithGoogle: (credential: string, termsAccepted: boolean) => Promise<void>
  register: (input: {
    username: string
    email: string
    password: string
    full_name: string
    terms_accepted: boolean
  }) => Promise<void>
  refreshUser: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      setLoading(false)
      return
    }
    authApi
      .me()
      .then((res) => setUser(res.data))
      .catch(() => {
        setStoredToken(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      async login(identity, password, remember = true) {
        const looksLikeEmail = identity.includes("@")
        try {
          const res = await authApi.login(
            looksLikeEmail ? { email: identity, password } : { username: identity, password },
          )
          setStoredToken(res.data.access_token, remember)
          const me = await authApi.me()
          setUser(me.data)
        } catch (err) {
          setStoredToken(null)
          setUser(null)
          throw err
        }
      },
      async loginWithGoogle(credential, termsAccepted) {
        try {
          const response = await authApi.googleLogin(credential, termsAccepted)
          setStoredToken(response.data.access_token)
          const me = await authApi.me()
          setUser(me.data)
        } catch (err) {
          setStoredToken(null)
          setUser(null)
          throw err
        }
      },
      async register(input) {
        try {
          await authApi.register(input)
          const res = await authApi.login({ username: input.username, password: input.password })
          setStoredToken(res.data.access_token)
          const me = await authApi.me()
          setUser(me.data)
        } catch (err) {
          setStoredToken(null)
          setUser(null)
          throw err
        }
      },
      async refreshUser() {
        const response = await authApi.me()
        setUser(response.data)
      },
      async logout() {
        try {
          await authApi.logout()
        } catch (error) {
          toast.error(`Signed out locally, but the server could not revoke the session: ${extractApiError(error)}`)
        }
        setStoredToken(null)
        setUser(null)
      },
    }),
    [user, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
