# SecureOps Enterprise Frontend Platform

The official React + TypeScript dashboard for the **SecureOps Enterprise AI Security Gateway**.

---

## 🚀 Getting Started

### 1. Prerequisites
- Node.js 18+ & npm
- SecureOps FastAPI Backend running at `http://127.0.0.1:8000`

### 2. Environment Setup
Copy the template environment file:
```bash
cp .env.example .env
```
Ensure `VITE_API_BASE_URL=http://127.0.0.1:8000` is set in `.env`.

### 3. Installation
```bash
npm install
```

### 4. Development Server
Start Vite local dev server:
```bash
npm run dev
```
Navigate to `http://localhost:3000`.

### 5. Production Build
```bash
npm run build
```

### 6. Run Unit Tests
```bash
npm run test
```
