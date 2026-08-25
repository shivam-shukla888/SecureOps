# SecureOps Frontend Architecture

The **SecureOps Frontend Platform** is a enterprise security operations dashboard built with React 18, Vite, TypeScript, and Tailwind CSS.

---

## 1. Directory Structure

```text
frontend/
├── src/
│   ├── components/
│   │   ├── layout/       # Sidebar, Topbar, GlassCard
│   │   └── views/        # All 13 primary application views
│   ├── context/          # AuthContext (API key, Tenant ID, User Role)
│   ├── services/         # API Client abstraction (`api.ts`)
│   ├── types/            # TypeScript Pydantic schema interfaces
│   ├── App.tsx           # Router & navigation layout
│   └── main.tsx          # Application entrypoint
├── API_CONTRACT.md
├── ARCHITECTURE.md
└── README.md
```

---

## 2. Key Architecture Decisions

- **TanStack Query (v5)**: Manages async state caching, automated refetching, and query invalidation upon approval or request execution.
- **Client-Side Auth Context**: Stores API keys safely in memory/localStorage and handles automatic `Bearer` header injection.
- **Server-Side Security Authority**: The frontend performs zero local policy evaluations. All risk classifications and permission checks are authoritative server-side decisions.
