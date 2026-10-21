import { Link } from "react-router-dom"

export default function VerifyEmailPage() {
  return (
    <main className="command-grid relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-8">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(8,145,178,0.13),transparent_48%)]" />
      <section className="glass-panel relative z-10 w-full max-w-md p-6 text-center sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-ice">Account access</p>
        <h1 className="mt-3 text-3xl font-semibold">Email verification removed</h1>
        <p className="mt-4 text-sm text-slate-300">
          Email verification is not part of DEIS sign-in. Use your username or email address and password to sign in.
        </p>
        <Link to="/login" className="mt-6 inline-block text-sm text-ice hover:underline">Return to sign in</Link>
      </section>
    </main>
  )
}
