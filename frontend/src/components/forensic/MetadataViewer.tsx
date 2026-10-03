import { ChevronDown } from "lucide-react"
import { useMemo, useState } from "react"
import type { MetadataPayload } from "@/types/api"

function groupMetadata(data: Record<string, unknown>) {
  const groups: Record<string, Array<[string, unknown]>> = {
    Identity: [],
    Cryptographic: [],
    File: [],
    Additional: [],
  }
  for (const [key, value] of Object.entries(data)) {
    const k = key.toLowerCase()
    if (k.includes("hash") || k.includes("sha") || k.includes("checksum")) groups.Cryptographic.push([key, value])
    else if (["filename", "extension", "mime_type", "file_size", "author", "title"].includes(k)) groups.Identity.push([key, value])
    else if (k.includes("exif") || k.includes("gps") || k.includes("created") || k.includes("modified")) groups.Additional.push([key, value])
    else groups.File.push([key, value])
  }
  return groups
}

function renderValue(value: unknown): string {
  if (value == null) return "—"
  if (typeof value === "object") return JSON.stringify(value, null, 2)
  return String(value)
}

export function MetadataViewer({ payload }: { payload: MetadataPayload }) {
  const groups = useMemo(() => groupMetadata(payload.metadata || {}), [payload.metadata])
  const [open, setOpen] = useState<Record<string, boolean>>({
    Identity: true,
    Cryptographic: true,
    File: false,
    Additional: true,
  })

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.18em] text-slate-400">
        <span>Type {payload.file_type}</span>
        <span>MIME {payload.mime_type || "unknown"}</span>
        <span>Extract {payload.extraction_status}</span>
      </div>
      {payload.extraction_errors?.length > 0 && (
        <div className="rounded-md border border-flare/30 bg-flare/10 p-3 text-sm text-flare">
          {payload.extraction_errors.join(" ")}
        </div>
      )}
      {Object.entries(groups).map(([name, rows]) =>
        rows.length ? (
          <section key={name} className="overflow-hidden rounded-lg border border-white/10">
            <button
              type="button"
              className="flex w-full items-center justify-between bg-white/5 px-4 py-3 text-left text-sm font-medium"
              onClick={() => setOpen((prev) => ({ ...prev, [name]: !prev[name] }))}
            >
              {name}
              <ChevronDown className={`h-4 w-4 transition ${open[name] ? "rotate-180" : ""}`} />
            </button>
            {open[name] && (
              <dl className="divide-y divide-white/5">
                {rows.map(([key, value]) => (
                  <div key={key} className="grid grid-cols-1 gap-1 px-4 py-3 text-sm sm:grid-cols-[160px_1fr] sm:gap-4">
                    <dt className="font-mono text-xs uppercase tracking-wider text-slate-500">{key}</dt>
                    <dd className="whitespace-pre-wrap break-all font-mono text-ice/90">{renderValue(value)}</dd>
                  </div>
                ))}
              </dl>
            )}
          </section>
        ) : null,
      )}
    </div>
  )
}
