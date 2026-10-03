import { AnimatePresence, motion } from "framer-motion"
import {
  FileSearch,
  Fingerprint,
  FolderOpen,
  LayoutDashboard,
  LogOut,
  ScrollText,
  Settings,
  ShieldCheck,
  Upload,
  FileBarChart,
  GitBranch,
} from "lucide-react"
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import { CreatorFooter } from "@/components/layout/CreatorFooter"
import { cn } from "@/lib/utils"

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/cases", label: "Cases", icon: FolderOpen },
  { to: "/evidence", label: "Evidence", icon: Fingerprint },
  { to: "/upload", label: "Upload Evidence", icon: Upload },
  { to: "/verify", label: "Verify Integrity", icon: ShieldCheck },
  { to: "/chain-of-custody", label: "Chain of Custody", icon: GitBranch },
  { to: "/metadata", label: "View Metadata", icon: FileSearch },
  { to: "/audit", label: "Audit Logs", icon: ScrollText },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/settings", label: "Settings", icon: Settings },
]

export function AppShell() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <div className="command-grid min-h-screen lg:grid lg:grid-cols-[248px_1fr]">
      <aside className="relative border-b border-white/10 bg-[#070b14]/90 backdrop-blur-xl lg:sticky lg:top-0 lg:h-screen lg:overflow-y-auto lg:border-b-0 lg:border-r">
        <div className="flex items-center gap-3 px-5 py-4 lg:py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-md border border-ice/40 bg-ice/10 text-ice shadow-glow">
            <Fingerprint className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.28em] text-ice">DEIS</p>
            <p className="max-w-40 text-xs leading-4 text-slate-300">Digital Evidence Integrity System</p>
          </div>
        </div>
        <nav aria-label="Primary navigation" className="forensic-nav flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:overflow-visible lg:pb-6">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "relative flex shrink-0 items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-400 transition hover:text-ice lg:w-full",
                  isActive && "text-ice",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.span
                      layoutId="nav-indicator"
                      className="absolute inset-0 rounded-lg border border-ice/30 bg-ice/10"
                      transition={{ type: "spring", stiffness: 380, damping: 32 }}
                    />
                  )}
                  <item.icon className="relative z-10 h-4 w-4" />
                  <span className="relative z-10">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="hidden px-5 pb-6 lg:block">
          <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Logged-in user</p>
          <p className="mt-1 text-sm">{user?.username}</p>
          <p className="truncate font-mono text-[11px] text-slate-500">{user?.email}</p>
          <button
            type="button"
            onClick={() => {
              logout()
              navigate("/login")
            }}
            className="mt-4 inline-flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-400 hover:text-flare"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
      </aside>
      <div className="min-w-0">
        <header className="flex items-center justify-between border-b border-white/10 px-4 py-3 lg:px-8">
          <div>
            <p className="text-[10px] uppercase tracking-[0.1em] text-slate-400">Digital Evidence Integrity System</p>
            <p className="font-mono text-xs text-ice/80">{location.pathname}</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 text-xs text-slate-500 sm:flex">
              <span className="h-2 w-2 rounded-full bg-mint shadow-glow" />
              System Online
            </div>
            <span className="hidden max-w-36 truncate border-l border-white/10 pl-3 text-xs text-slate-400 md:block">
              {user?.username}
            </span>
            <button
              type="button"
              aria-label="Sign out"
              title="Sign out"
              onClick={() => {
                logout()
                navigate("/login")
              }}
              className="rounded-md border border-white/10 p-2 text-slate-400 transition hover:border-flare/40 hover:text-flare lg:hidden"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>
        <AnimatePresence mode="wait">
          <motion.main
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.22 }}
            className="px-4 py-6 lg:px-8"
          >
            <Outlet />
            <CreatorFooter className="mt-10 border-t border-white/10 pt-5" />
          </motion.main>
        </AnimatePresence>
      </div>
    </div>
  )
}
