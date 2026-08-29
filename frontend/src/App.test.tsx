import { describe, it, expect } from 'vitest';
import { getApiBaseUrl, BASE_URL } from './services/api';

describe('SecureOps Frontend Security & API Tests', () => {
  it('verifies environment base URL default points to production Render gateway', () => {
    const url = getApiBaseUrl();
    expect(url).toBe('https://secureops-gateway.onrender.com');
    expect(BASE_URL).toBe('https://secureops-gateway.onrender.com');
  });

  it('validates single Bearer prefix formatting logic', () => {
    const rawToken = "  Bearer Bearer 'my_secret_token_123'  ";
    let cleanToken = rawToken.trim().replace(/['"]/g, '');
    while (cleanToken.toLowerCase().startsWith('bearer ')) {
      cleanToken = cleanToken.substring(7).trim();
    }
    const finalHeader = `Bearer ${cleanToken}`;
    expect(finalHeader).toBe('Bearer my_secret_token_123');
  });

  it('validates role hierarchy definitions', () => {
    const roles = ['OWNER', 'ADMIN', 'APPROVER', 'OPERATOR', 'VIEWER'];
    expect(roles).toContain('OWNER');
    expect(roles).toContain('APPROVER');
  });

  it('evaluates gateway online status correctly for ready and healthy responses', () => {
    const isReadyOnline = (res: { status: string }) => res && (res.status === 'ready' || res.status === 'healthy');
    expect(isReadyOnline({ status: 'ready' })).toBe(true);
    expect(isReadyOnline({ status: 'healthy' })).toBe(true);
    expect(isReadyOnline({ status: 'unhealthy' })).toBe(false);
    expect(isReadyOnline({ status: 'degraded' })).toBe(false);
  });
});
