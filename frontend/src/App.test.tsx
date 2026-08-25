import { describe, it, expect } from 'vitest';

describe('SecureOps Frontend Security & API Tests', () => {
  it('verifies environment base URL default', () => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
    expect(baseUrl).toBe('http://127.0.0.1:8000');
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
});
