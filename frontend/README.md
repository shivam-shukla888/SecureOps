# SecureOps Enterprise Frontend Console

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live%20Dashboard-black.svg?logo=vercel)](https://secure-ops-pi.vercel.app)
[![Vitest](https://img.shields.io/badge/Vitest-39%20Passed-brightgreen.svg?logo=vitest)]()
[![React](https://img.shields.io/badge/React-18-cyan.svg?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue.svg?logo=typescript)](https://www.typescriptlang.org/)

The official enterprise security operations console for the **SecureOps Universal AI Security Gateway**.

---

## 🌐 Live Production Deployments

- **Live Console**: [https://secure-ops-pi.vercel.app](https://secure-ops-pi.vercel.app)
- **API Gateway**: [https://secureops-gateway.onrender.com](https://secureops-gateway.onrender.com)
- **Liveness Probe (`/health`)**: [https://secureops-gateway.onrender.com/health](https://secureops-gateway.onrender.com/health)
- **Readiness Probe (`/ready`)**: [https://secureops-gateway.onrender.com/ready](https://secureops-gateway.onrender.com/ready)

### Governed Dashboard Deep Links
- 📊 **Overview**: [https://secure-ops-pi.vercel.app/dashboard](https://secure-ops-pi.vercel.app/dashboard)
- 🛡️ **Request Gateway**: [https://secure-ops-pi.vercel.app/gateway](https://secure-ops-pi.vercel.app/gateway)
- ✋ **Approval Center**: [https://secure-ops-pi.vercel.app/approvals](https://secure-ops-pi.vercel.app/approvals)
- 🚨 **Security Events**: [https://secure-ops-pi.vercel.app/security-events](https://secure-ops-pi.vercel.app/security-events)
- 📜 **Audit Explorer**: [https://secure-ops-pi.vercel.app/audit](https://secure-ops-pi.vercel.app/audit)
- ⚡ **Execution Center**: [https://secure-ops-pi.vercel.app/executions](https://secure-ops-pi.vercel.app/executions)
- 🔧 **Tool Governance**: [https://secure-ops-pi.vercel.app/tools](https://secure-ops-pi.vercel.app/tools)
- 🏢 **Multi-Tenancy**: [https://secure-ops-pi.vercel.app/tenants](https://secure-ops-pi.vercel.app/tenants)
- 👥 **Users & Roles**: [https://secure-ops-pi.vercel.app/rbac](https://secure-ops-pi.vercel.app/rbac)
- 🔑 **API Credentials**: [https://secure-ops-pi.vercel.app/credentials](https://secure-ops-pi.vercel.app/credentials)
- 🩺 **System Health**: [https://secure-ops-pi.vercel.app/health](https://secure-ops-pi.vercel.app/health)
- ⚙️ **Settings**: [https://secure-ops-pi.vercel.app/settings](https://secure-ops-pi.vercel.app/settings)

---

## 🚀 Getting Started

### 1. Prerequisites
- Node.js 18+ & npm
- SecureOps FastAPI Gateway running locally or on Render

### 2. Environment Setup
```bash
cp .env.example .env
```
Ensure `VITE_API_BASE_URL=https://secureops-gateway.onrender.com` (or `http://127.0.0.1:8000` for local dev).

### 3. Installation
```bash
npm install
```

### 4. Development Server
```bash
npm run dev
```
Navigate to [http://localhost:5173](http://localhost:5173) (or `http://localhost:3000`).

### 5. Run Unit & Regression Tests
```bash
npm run test
```

### 6. Production Build
```bash
npm run build
```
Builds the production bundle into `dist/` with Vercel SPA client-side routing support (`vercel.json`).
