export function PageHeader({ kicker, title, detail }: { kicker: string; title: string; detail?: string }) {
  return (
    <div className="mb-8">
      <p className="text-[11px] uppercase tracking-[0.28em] text-ice/80">{kicker}</p>
      <h1 className="mt-1 text-3xl font-semibold tracking-wide">{title}</h1>
      {detail && <p className="mt-2 max-w-2xl text-sm text-slate-400">{detail}</p>}
    </div>
  )
}
