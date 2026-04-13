
# Activity Registration and Funding Audit Management Platform


## 🧭 System Overview
A production-structured full-stack platform for managing **activity applications**, **review workflows (FSM)**, **funding/budget operations**, **file/material submissions (versioned)**, and **auditable actions** with role-based access control.

- **Inferred product name in code**: “Activity Registration and Funding Audit Platform” (FastAPI app title) / “Activity Audit Platform” (UI header)
- **Primary runtime**: Vue 3 SPA + FastAPI API + PostgreSQL (Docker Compose)

## 🏛️ Architecture
- **Client**: Vue 3 + Pinia + Vue Router (Vite dev server + `/api` proxy to backend)
- **Server**: FastAPI (sync endpoints + middleware) + SQLAlchemy 2.0 ORM
- **Data**: PostgreSQL 16 (no SQLite fallback enforced)
- **Storage**: Local filesystem for uploads (`/app/uploads` volume) and exports/backups (`/exports`, `/backups` mounts)
- **Background jobs**: APScheduler in-process (metrics snapshots, maintenance/GC, idempotency cleanup, daily backup)

## 🖥️ Frontend (Vue 3)
- **Routing**: `/login`, `/register`, `/applications`, `/files`, `/workflow`, `/finance` with per-route permission gate via `meta.permission`
- **State**: Pinia stores for auth, applications, workflow, finance, UI (toasts/inline error, sidebar collapse)
- **API access**: `fetch` wrapper with Bearer token from `sessionStorage`, lightweight GET caching (8s TTL), logs `X-Correlation-ID`
- **Core screens**
  - **Applications**: create wizard + list table
  - **Files**: multi-file queue + progress simulation + retry/cancel
  - **Workflow**: review list, apply transitions, view application history
  - **Finance**: set budget, add expense with overspend confirmation modal, list transactions

## 🧩 Backend (FastAPI)
- **Entry**: `server/app/main.py` wires routers under `/api/v1`, adds middlewares, schedules jobs, initializes DB and bootstrap data
- **API modules**:
  - **Auth**: register/login/refresh/logout/me (`/api/v1/auth/*`)
  - **Applications**: create/list with role-aware filtering (`/api/v1/applications`)
  - **Workflow**: transition, batch-review, list reviews, history (`/api/v1/workflow/*`)
  - **Finance**: budget, transactions, invoice upload (`/api/v1/finance/*`)
  - **Files**: material upload (`/api/v1/files/upload`)
  - **Metrics**: latest snapshot (`/api/v1/metrics/latest`)
  - **System**: exports (CSV), user provisioning, backup/restore endpoints (admin-only) (`/api/v1/system/*`)

## 🗃️ Database (PostgreSQL + SQLAlchemy)
**Core tables (models):**
- **Identity/RBAC**: `users`, `roles`, `refresh_tokens`, `revoked_tokens`
- **Applications & workflow**: `applications`, `workflow_transitions` (seeded), `application_history`
- **Materials/files**: `materials`, `material_versions` (sha256, size, label, correction_reason; version cap behavior in service)
- **Finance**: `budgets` (lock after txn activity), `transactions`, `invoice_attachments`
- **Audit/observability**: `logs` (append-only enforcement), `endpoint_observations`
- **Ops/reliability**: `idempotency_records` (scope+key unique), `job_locks`, `metric_snapshots`
- **Additional**: `export_records`, `data_collection_batches`, `quality_validation_results` (present, minimal usage in read paths)

## 🔐 Security
- **Authentication**: JWT access + refresh tokens (token “typ” enforced), refresh rotation, refresh-family reuse detection, JTI revocation list
- **Account lockout**: 10 failed attempts in 5 minutes → 30-minute lock
- **Authorization**: static role→permission policy (`applicant`, `reviewer`, `financial_admin`, `system_admin`) with `require_permission()` dependency
- **Audit of authz decisions**: each permission check logs ALLOW/DENY to immutable `logs`
- **Data minimization**: application listing masks applicant contact fields based on viewer role
- **Public registration toggle**: can be disabled via `ENABLE_PUBLIC_REGISTRATION`

## 🔁 Workflow & Business Rules
- **Workflow FSM**: deterministic transition matrix (e.g., `Submitted → Approved/Rejected/...`, `Supplemented → Approved/Rejected`, rejection requires reason)
- **Optimistic concurrency**: application `version` must match `expected_version` for transitions; mismatches return 409
- **Idempotency**: required `Idempotency-Key` header for critical mutating endpoints (workflow, finance, file upload); server stores/replays responses per `(scope,key)` with payload hashing
- **Files/materials**:
  - Allowed MIME/ext: PDF/JPEG/PNG; single file ≤ 20MB; per-application total ≤ 200MB
  - Supplement window: after deadline up to 72 hours, single-use, requires correction reason
  - Duplicate detection by SHA-256 across material versions
- **Finance**:
  - Budget must be set before transactions
  - Budget becomes locked after any transaction
  - Overspending confirmation flow when projected expenses exceed 110% of budget

## 🧱 Reliability & Resilience
- **Transactional boundaries**: explicit unit-of-work for critical writes; row locking via `SELECT ... FOR UPDATE` in repositories
- **Conflict signaling**: concurrent operations surface as 409 conflicts (version mismatch / OperationalError handling)
- **Background job singletons**: DB-backed `job_locks` to avoid duplicate execution across instances
- **Storage hygiene**: startup recovery scan + periodic maintenance removes orphan temp files, enforces disk limits, GC for stale versions
- **Backups**: scheduled daily `pg_dump` with 7-day retention; restore via `pg_restore --clean --if-exists`

## 📈 Observability
- **Correlation IDs**: `X-Correlation-ID` generated/propagated per request and echoed in responses
- **Endpoint telemetry**: latency/status/method/path stored in `endpoint_observations` (best-effort, failure-tolerant)
- **Audit log**: `logs` table designed as append-only (ORM event hooks + DB triggers on PostgreSQL)

## 🧪 Testing
- **Backend**: `pytest` with FastAPI `TestClient`, including RBAC, FSM validation, concurrency races, idempotency replay, file constraints, finance rules, history endpoint, soak-style stability test
- **Frontend**: Playwright E2E covering register/login, application create, file upload (API), reviewer transition, and history view
- **Test orchestration**: `docker-compose.test.yml` spins Postgres (tmpfs), runs backend tests, then E2E against a health-checked API + Vite dev server

## 🚀 Deployment
- **Local/dev**: `docker-compose.yml` runs `db`, `server`, `client` with exposed ports 5432/8000/5173, healthchecks, persistent volumes for DB and uploads
- **Prod-like**: `docker-compose.prod.yml` similar topology with secrets via env vars, persistent volumes, and exports/backups mounts
- **Required env**: `DATABASE_URL`, `JWT_SECRET`, `ENCRYPTION_KEY` (enforced on server start; PostgreSQL-only)
