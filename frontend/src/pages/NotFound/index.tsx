import { Link } from "react-router-dom"

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
      <p className="font-mono text-ice">404</p>
      <h1 className="mt-2 text-3xl">Page not found</h1>
      <Link to="/dashboard" className="mt-4 text-sm text-ice hover:underline">
        Return to dashboard
      </Link>
    </div>
  )
}
