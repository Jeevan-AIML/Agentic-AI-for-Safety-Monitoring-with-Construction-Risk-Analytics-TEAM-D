import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Layout
import AppShell from '@/components/layout/AppShell';
import { ProtectedRoute, GuestRoute } from '@/components/layout/ProtectedRoute';

// Pages
import LoginPage from '@/pages/Login/LoginPage';
import DashboardPage from '@/pages/Dashboard/DashboardPage';
import ProjectsPage from '@/pages/Projects/ProjectsPage';
import CreateProjectPage from '@/pages/Projects/CreateProjectPage';
import SitesPage from '@/pages/Sites/SitesPage';
import SiteDetailPage from '@/pages/Sites/SiteDetailPage';
import CreateSitePage from '@/pages/Sites/CreateSitePage';
import RiskMonitoringPage from '@/pages/RiskMonitoring/RiskMonitoringPage';
import NotificationsPage from '@/pages/Notifications/NotificationsPage';
import UsersPage from '@/pages/Users/UsersPage';
import SafetyPage from '@/pages/Safety/SafetyPage';
import CompliancePage from '@/pages/Compliance/CompliancePage';
import InsurancePage from '@/pages/Insurance/InsurancePage';
import {
  IncidentsPage, InspectionsPage, ReportsPage, SettingsPage,
  NotFoundPage, UnauthorizedPage
} from '@/pages/Placeholders';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 10000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Guest routes */}
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<LoginPage />} />
          </Route>

          {/* Protected app routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<DashboardPage />} />

              {/* Projects */}
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/projects/new" element={<CreateProjectPage />} />
              <Route path="/projects/:projectId" element={<ProjectsPage />} />

              {/* Sites */}
              <Route path="/sites" element={<SitesPage />} />
              <Route path="/sites/new" element={<CreateSitePage />} />
              <Route path="/sites/:siteId" element={<SiteDetailPage />} />

              {/* Risk Monitoring */}
              <Route path="/risk-monitoring" element={<RiskMonitoringPage />} />

              {/* Placeholders */}
              <Route path="/safety" element={<SafetyPage />} />
              <Route path="/compliance" element={<CompliancePage />} />
              <Route path="/insurance" element={<InsurancePage />} />
              <Route path="/incidents" element={<IncidentsPage />} />
              <Route path="/inspections" element={<InspectionsPage />} />
              <Route path="/reports" element={<ReportsPage />} />

              {/* System */}
              <Route path="/notifications" element={<NotificationsPage />} />
              <Route element={<ProtectedRoute allowedRoles={['super_admin']} />}>
                <Route path="/users" element={<UsersPage />} />
              </Route>
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Route>

          {/* System pages */}
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route path="/404" element={<NotFoundPage />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3500,
          style: {
            background: '#0f172a',
            color: '#e2e8f0',
            border: '1px solid #1e293b',
            borderRadius: '10px',
            fontSize: '13px',
          },
          success: {
            iconTheme: { primary: '#22c55e', secondary: '#0f172a' },
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#0f172a' },
          },
        }}
      />
    </QueryClientProvider>
  );
}
