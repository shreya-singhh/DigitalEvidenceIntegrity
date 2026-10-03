import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { Toaster } from "sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { AppShell } from "@/components/layout/AppShell"
import { ProtectedRoute } from "@/components/layout/ProtectedRoute"
import { AuthProvider } from "@/context/AuthContext"
import LoginPage from "@/pages/Login"
import RegisterPage from "@/pages/Register"
import DashboardPage from "@/pages/Dashboard"
import CasesPage from "@/pages/Cases"
import CaseDetailPage from "@/pages/Cases/Detail"
import EvidencePage from "@/pages/Evidence"
import EvidenceDetailPage from "@/pages/Evidence/Detail"
import UploadPage from "@/pages/Upload"
import MetadataPage from "@/pages/Metadata"
import VerifyPage from "@/pages/Verify"
import ChainOfCustodyPage from "@/pages/ChainOfCustody"
import AuditPage from "@/pages/Audit"
import ReportsPage from "@/pages/Reports"
import SettingsPage from "@/pages/Settings"
import NotFoundPage from "@/pages/NotFound"

export default function App() {
  return (
    <TooltipProvider delayDuration={200}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/cases" element={<CasesPage />} />
                <Route path="/cases/:caseId" element={<CaseDetailPage />} />
                <Route path="/evidence" element={<EvidencePage />} />
                <Route path="/evidence/:evidenceId" element={<EvidenceDetailPage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/metadata" element={<MetadataPage />} />
                <Route path="/metadata/:evidenceId" element={<MetadataPage />} />
                <Route path="/verify" element={<VerifyPage />} />
                <Route path="/verify/:evidenceId" element={<VerifyPage />} />
                <Route path="/chain-of-custody" element={<ChainOfCustodyPage />} />
                <Route path="/audit" element={<AuditPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster theme="dark" position="top-right" />
      </AuthProvider>
    </TooltipProvider>
  )
}
