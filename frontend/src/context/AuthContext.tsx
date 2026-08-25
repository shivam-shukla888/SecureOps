import React, { createContext, useContext, useState, useEffect } from 'react';
import { RoleEnum } from '../types/api';

interface AuthContextType {
  apiKey: string;
  setApiKey: (key: string) => void;
  tenantId: string;
  setTenantId: (tenant: string) => void;
  userRole: RoleEnum;
  setUserRole: (role: RoleEnum) => void;
  userId: string;
  setUserId: (id: string) => void;
  isAuthenticated: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Use sessionStorage to ensure credentials expire when the browser tab/session closes
  const [apiKey, setApiKey] = useState<string>(() => sessionStorage.getItem('secureops_session_key') || '');
  const [tenantId, setTenantId] = useState<string>(() => sessionStorage.getItem('secureops_tenant_id') || 'tenant_default');
  const [userRole, setUserRole] = useState<RoleEnum>('OWNER');
  const [userId, setUserId] = useState<string>('admin_operator');

  useEffect(() => {
    if (apiKey) {
      sessionStorage.setItem('secureops_session_key', apiKey.trim());
    } else {
      sessionStorage.removeItem('secureops_session_key');
    }
  }, [apiKey]);

  useEffect(() => {
    sessionStorage.setItem('secureops_tenant_id', tenantId);
  }, [tenantId]);

  const logout = () => {
    setApiKey('');
    sessionStorage.removeItem('secureops_session_key');
  };

  return (
    <AuthContext.Provider
      value={{
        apiKey,
        setApiKey,
        tenantId,
        setTenantId,
        userRole,
        setUserRole,
        userId,
        setUserId,
        isAuthenticated: Boolean(apiKey),
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
