import { motion } from "framer-motion"
import { UploadCloud } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"

const ACCEPTED = ".pdf,.jpg,.jpeg,.png,.mp4,.mp3,.docx,.txt"

export function DropZone({
  onFile,
  scanning,
  fileName,
}: {
  onFile: (file: File) => void
  scanning?: boolean
  fileName?: string
}) {
  const [over, setOver] = useState(false)

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setOver(false)
        const file = e.dataTransfer.files[0]
        if (file) onFile(file)
      }}
      className={cn(
        "relative flex min-h-56 cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border border-dashed border-ice/30 bg-[#071018] px-6 text-center transition",
        over && "border-ice bg-ice/5",
      )}
    >
      {scanning && (
        <motion.div
          className="pointer-events-none absolute inset-x-8 h-16 bg-gradient-to-b from-transparent via-ice/25 to-transparent"
          animate={{ y: ["-40%", "180%"] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: "linear" }}
        />
      )}
      <UploadCloud className="mb-3 h-10 w-10 text-ice" />
      <p className="text-lg font-medium">Choose a file or drop it here to upload</p>
      <p className="mt-1 max-w-md text-sm text-slate-400">
        A SHA-256 hash is calculated when evidence is uploaded. Supported: PDF, images, audio, video, DOCX, and TXT · 25 MB maximum.
      </p>
      {fileName && <p className="mt-3 font-mono text-xs text-ice">{scanning ? "Scanning" : "Queued"} · {fileName}</p>}
      <input
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onFile(file)
        }}
      />
    </label>
  )
}
