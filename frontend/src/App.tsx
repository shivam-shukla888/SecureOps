import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Sidebar } from './components/layout/Sidebar';
import { Topbar } from './components/layout/Topbar';

import { LoginView } from './components/views/LoginView';
import { DashboardView } from './components/views/DashboardView';
import { RequestGatewayView } from './components/views/RequestGatewayView';
import { ApprovalCenterView } from './components/views/ApprovalCenterView';
import { SecurityEventsView } from './components/views/SecurityEventsView';
import { AuditExplorerView } from './components/views/AuditExplorerView';
import { ExecutionCenterView } from './components/views/ExecutionCenterView';
import { ToolsView } from './components/views/ToolsView';
import { TenantsView } from './components/views/TenantsView';
import { RbacView } from './components/views/RbacView';
import { CredentialsView } from './components/views/CredentialsView';
import { HealthView } from './components/views/HealthView';
import { SettingsView } from './components/views/SettingsView';

export const App: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginView />;
  }

  return (
    <div className="flex min-h-screen bg-[#090d16]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar />
        <main className="flex-1 p-6 overflow-y-auto">
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
        </main>
      </div>
    </div>
  );
};
