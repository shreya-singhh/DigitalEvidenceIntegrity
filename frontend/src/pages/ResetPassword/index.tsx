import { Link } from "react-router-dom"

export default function ResetPasswordPage() {
  return (
    <main className="command-grid relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-8">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(8,145,178,0.13),transparent_48%)]" />
      <section className="glass-panel relative z-10 w-full max-w-md p-6 sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-ice">Account recovery</p>
        <h1 className="mt-3 text-3xl font-semibold">Password reset unavailable</h1>
        <p className="mt-5 text-sm text-slate-400">
          Password reset is not supported by the current DEIS backend. Contact your DEIS administrator for help.
        </p>
        <p className="mt-6 text-sm text-slate-500">
          <Link to="/login" className="text-ice hover:underline">Return to sign in</Link>
        </p>
      </section>
    </main>
  )
}
