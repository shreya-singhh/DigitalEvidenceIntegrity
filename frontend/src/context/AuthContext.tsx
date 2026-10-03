import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { authApi, getStoredToken, setStoredToken } from "@/lib/api"
import type { User } from "@/types/api"

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (identity: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
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
      async login(identity, password) {
        const looksLikeEmail = identity.includes("@")
        try {
          const res = await authApi.login(
            looksLikeEmail ? { email: identity, password } : { username: identity, password },
          )
          setStoredToken(res.data.access_token)
          const me = await authApi.me()
          setUser(me.data)
        } catch (err) {
          setStoredToken(null)
          setUser(null)
          throw err
        }
      },
      async register(username, email, password) {
        try {
          await authApi.register({ username, email, password })
          const res = await authApi.login({ username, password })
          setStoredToken(res.data.access_token)
          const me = await authApi.me()
          setUser(me.data)
        } catch (err) {
          setStoredToken(null)
          setUser(null)
          throw err
        }
      },
      logout() {
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
