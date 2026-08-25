# SecureOps Project Directory Structure

This document outlines the final repository layout, directory hierarchy, and structural organization of **SecureOps**.

---

```text
SecureOps/
├── secureops/
│   ├── app/                         # Core FastAPI Gateway Application
│   │   ├── main.py                  # API Gateway Routes & Exception Handlers
│   │   ├── config.py                # Configuration & Startup Security Validator
│   │   ├── schemas/                 # Pydantic Schemas (Request, Decision, Approval, Execution, Credential)
│   │   ├── security/                # Security Subsystems (Auth, RBAC, Policy, Rate Limit, Secrets, Network, HMAC, Idempotency)
│   │   ├── ai/                      # AI Providers (Gemini Flash -> Groq Fallback Classifier)
│   │   ├── tools/                   # Tool Registry, Permission Engine & DocumentService Adapter
│   │   ├── approval/                # Human-In-The-Loop Approval Ticket Lifecycle Manager
│   │   ├── audit/                   # Audit Logger, Repository, Metrics Tracker & SIEM Exporters
│   │   ├── db/                      # SQLAlchemy Async Engine, ORM Models & Parameterized Safe DB Query Adapter
│   │   ├── executor/                # Execution Dispatcher & Timeout Controller
│   │   └── n8n/                     # HMAC-Signed Outbound n8n Webhook Client
│   ├── tests/                       # 88-Test Pytest Suite (Adversarial, Auth, Policy, Multi-Tenancy, SSRF)
│   ├── alembic/                     # Database Migration Scripts
│   ├── scripts/                     # Operational Scripts (e2e_demo.py, demo.py, secret_scan.py, benchmark.py)
│   ├── Dockerfile                   # Multi-Stage Non-Root Production Dockerfile
│   ├── alembic.ini                  # Alembic Configuration File
│   └── requirements.txt             # Python Package Dependencies
├── security/                        # Security Threat Analysis & Checklist Documentation
│   ├── threat_model.md              # 21 STRIDE Threat Category Evaluation
│   ├── attack_cases.md              # 19 Automated Attack Case Inventory
│   └── security_checklist.md        # Operational Deployment Checklist
├── reference/                       # Historical Prototype Artifacts
│   └── n8n/                         # Original n8n Prototype JSON Workflows
│       ├── SecureOps.json           # Prototype Classifier Workflow
│       └── Secure Executor.json     # Prototype Executor Workflow
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions CI/CD Pipeline
├── docker-compose.yml               # Multi-Container Production Docker Compose Setup
├── .env.example                     # Environment Configuration Template
├── .gitignore                       # Git Exclusion Policy
├── README.md                        # Primary Repository Documentation & Quickstart
├── ARCHITECTURE.md                  # Comprehensive Architecture & Deployment Options
├── SECURITY.md                      # Security Policy & Vulnerability Governance
├── SECURITY_SCORECARD.md            # Objective 17-Point Security Scorecard
├── PRODUCT.md                       # Product Strategy & Business Value Proposition
├── DEMO.md                          # 3-Minute Demonstration Script
├── PERFORMANCE.md                   # Micro-Benchmark & Latency Profiles
└── PROJECT_STRUCTURE.md             # Repository Directory Layout Guide (This File)
```

---

## Directory Descriptions

| Path | Purpose |
| :--- | :--- |
| **`secureops/app/`** | Production application codebase containing routing, security policy engine, AI providers, tool permission engine, audit loggers, and database abstractions. |
| **`secureops/tests/`** | Full pytest regression and adversarial security test suite (88 passing tests). |
| **`secureops/scripts/`** | Operational scripts for secret scanning, micro-benchmarking, demo execution, and E2E validation. |
| **`secureops/alembic/`** | Database schema migration history and environment scripts. |
| **`security/`** | Comprehensive STRIDE threat model, attack case catalog, and deployment checklists. |
| **`reference/n8n/`** | Archival prototype n8n workflow JSON files retained for historical reference. |
| **`.github/workflows/`** | Automated CI/CD workflow executing secret scanning, test suites, and Docker builds. |
