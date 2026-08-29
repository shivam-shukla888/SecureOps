import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Sidebar } from './components/layout/Sidebar';
import { Topbar } from './components/layout/Topbar';

// Route-level code-splitting for optimal production bundle performance
const LoginView = lazy(() => import('./components/views/LoginView').then((m) => ({ default: m.LoginView })));
const DashboardView = lazy(() => import('./components/views/DashboardView').then((m) => ({ default: m.DashboardView })));
const RequestGatewayView = lazy(() => import('./components/views/RequestGatewayView').then((m) => ({ default: m.RequestGatewayView })));
const ApprovalCenterView = lazy(() => import('./components/views/ApprovalCenterView').then((m) => ({ default: m.ApprovalCenterView })));
const SecurityEventsView = lazy(() => import('./components/views/SecurityEventsView').then((m) => ({ default: m.SecurityEventsView })));
const AuditExplorerView = lazy(() => import('./components/views/AuditExplorerView').then((m) => ({ default: m.AuditExplorerView })));
const ExecutionCenterView = lazy(() => import('./components/views/ExecutionCenterView').then((m) => ({ default: m.ExecutionCenterView })));
const ToolsView = lazy(() => import('./components/views/ToolsView').then((m) => ({ default: m.ToolsView })));
const TenantsView = lazy(() => import('./components/views/TenantsView').then((m) => ({ default: m.TenantsView })));
const RbacView = lazy(() => import('./components/views/RbacView').then((m) => ({ default: m.RbacView })));
const CredentialsView = lazy(() => import('./components/views/CredentialsView').then((m) => ({ default: m.CredentialsView })));
const HealthView = lazy(() => import('./components/views/HealthView').then((m) => ({ default: m.HealthView })));
const SettingsView = lazy(() => import('./components/views/SettingsView').then((m) => ({ default: m.SettingsView })));

const ViewLoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center min-h-[50vh] text-slate-500 font-mono text-xs select-none">
    <div className="flex flex-col items-center gap-3">
      <div className="w-6 h-6 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
      <span>Loading SecureOps Console...</span>
    </div>
  </div>
);

export const App: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <Suspense fallback={<ViewLoadingFallback />}>
        <LoginView />
      </Suspense>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#090d16]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar />
        <main className="flex-1 p-6 overflow-y-auto">
          <Suspense fallback={<ViewLoadingFallback />}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardView />} />
              <Route path="/gateway" element={<RequestGatewayView />} />
              <Route path="/approvals" element={<ApprovalCenterView />} />
              <Route path="/security-events" element={<SecurityEventsView />} />
              <Route path="/audit" element={<AuditExplorerView />} />
              <Route path="/executions" element={<ExecutionCenterView />} />
              <Route path="/tools" element={<ToolsView />} />
              <Route path="/tenants" element={<TenantsView />} />
              <Route path="/rbac" element={<RbacView />} />
              <Route path="/credentials" element={<CredentialsView />} />
              <Route path="/health" element={<HealthView />} />
              <Route path="/settings" element={<SettingsView />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  );
};
