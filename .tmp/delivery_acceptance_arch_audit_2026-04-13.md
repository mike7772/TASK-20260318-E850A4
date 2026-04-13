## 1. Verdict

- **Overall conclusion: Partial Pass**
  - **Rationale**: The backend shows meaningful implementation for core flows (RBAC, workflow FSM, file upload limits/versioning/duplicate detection, finance overspend confirmation, backups, encrypted config, audit logs) with non-trivial tests. However, there are material delivery/security concerns (hardcoded secrets in compose, some auth token/logout design issues, and major frontend requirement gaps vs the Prompt).

---

## 2. Scope and Static Verification Boundary

- **What was reviewed (static)**:
  - Documentation and deployment manifests: `README.md`, `docker-compose*.yml`, `run_test.sh`, `CONSISTENCY_MODEL.md`
  - Backend entrypoints, routers, security, core services/models: `server/app/**`
  - Backend tests: `server/tests/**`
  - Frontend key pages/services and Playwright tests: `client/src/**`, `client/tests/**`, `client/playwright.config.ts`
- **What was not reviewed**:
  - Runtime behavior, UI rendering, database migrations applied at runtime, Docker images, scheduler behavior under real deployment.
  - Any “works in container / works in browser” claim not proven by static code + tests.
- **What was intentionally not executed**:
  - No project startup, no Docker, no tests, no DB, no browser automation.
- **Claims requiring follow-up**:
  - **Manual Verification Required**: production deployment hardening (secrets management, TLS, reverse proxy), backup/restore success (`pg_dump`/`pg_restore` availability), and offline-only constraints.

---

## 3. Repository / Requirement Mapping Summary

- **Prompt’s core business goal**: English activity registration + material checklist uploads (type/size limits, versioning up to 3, deadline lock + one-time 72h supplementary with correction reason), reviewer state-machine workflow with batch review (≤50), traceable logs, finance transactions + overspend warning requiring secondary confirmation, Postgres local/offline storage, local disk file storage with SHA-256 fingerprint, reserved similarity endpoint disabled by default, strong password hashing, role-based masking, lockout policy, permission isolation, access auditing, encrypted sensitive config, daily backups + one-click recovery, export of audit/compliance/whitelist reports.
- **Main implementation areas mapped**:
  - **Backend**: FastAPI app + routers in `server/app/main.py` and `server/app/api/v1/routers/*`; RBAC in `server/app/api/v1/deps.py` + `server/app/core/policy_engine.py`; workflow FSM (`server/app/core/state_machine.py` + `server/app/services/workflow_service.py`); file upload/versioning/sha256 (`server/app/services/file_service.py` + `server/app/services/validation_service.py`); finance overspend confirmation (`server/app/services/finance_service.py`); backups/recovery/export/config secret (`server/app/api/v1/routers/system.py`, `server/app/services/backup_service.py`, `server/app/services/config_service.py`, `server/app/core/crypto_config.py`); audit logs model (`server/app/models/models.py`) and middleware (`server/app/middleware/*`).
  - **Frontend**: key pages in `client/src/features/**` and API wrappers in `client/src/services/**`; Playwright E2E flow in `client/tests/app.spec.ts`.

---

## 4. Section-by-section Review

### 4.1 Documentation and static verifiability (Hard Gate 1.1)

- **Startup / run / test / configuration instructions**
  - **Conclusion: Partial Pass**
  - **Rationale**: README provides environment variables and Docker-based startup and test instructions, but is Docker-centric (prompt emphasizes pure offline/local deployment; Docker is compatible but not the only offline path). Test script mandates Docker.
  - **Evidence**: `README.md:22-72`, `run_test.sh:1-20`
  - **Manual verification note**: verify non-Docker offline run procedure if required by delivery expectations.

- **Documented entry points / config / structure consistent with repo**
  - **Conclusion: Pass**
  - **Rationale**: README structure matches `client/` + `server/`, API/ports align with compose; backend enforces PostgreSQL-only.
  - **Evidence**: `README.md:15-59`, `docker-compose.yml:21-55`, `server/app/db/session.py:5-11`, `server/app/main.py:67-86`

- **Enough static evidence to attempt verification**
  - **Conclusion: Pass**
  - **Rationale**: Clear routers, schemas, tests, and deployment manifests exist; reviewer can follow static paths without rewriting core code.
  - **Evidence**: `server/app/main.py:67-86`, `server/tests/test_rules.py:22-269`, `client/tests/app.spec.ts:12-53`

### 4.2 Prompt deviation (Hard Gate 1.2)

- **Conclusion: Partial Pass**
- **Rationale**: Backend aligns well with many Prompt requirements; frontend UX is significantly thinner than Prompt’s “form wizard + checklist-driven upload item-by-item + deadline lock + labeled statuses” and relies on manual IDs/types rather than guided checklist selection. Some key semantics are implemented but not matching the described “one-time supplementary submission process initiated” (backend treats any post-deadline upload with a correction reason as supplemental).
- **Evidence**:
  - Minimal wizard subset and manual upload inputs: `client/src/features/applications/ApplicationWizardPage.vue:56-69`, `client/src/features/files/FileUploadPage.vue:5-7`
  - Checklist fetched but not used for structured checklist-driven upload: `client/src/features/files/FileUploadPage.vue:44-55`
  - Supplemental logic implicit in upload validation: `server/app/services/validation_service.py:29-39`, `server/app/services/file_service.py:49-53`

---

## 5. Delivery Completeness

### 5.1 Coverage of explicitly stated core functional requirements (2.1)

- **Applicants: wizard + materials upload/versioning/locking**
  - **Conclusion: Partial Pass**
  - **Rationale**:
    - Backend enforces allowed types and size limits, caps versions at 3, stores SHA-256, checks duplicates, enforces applicant object-level ownership on upload, and enforces 72h supplementary once with correction reason.
    - Frontend does not implement checklist-driven item-by-item upload UX, material label states, deadline locking feedback, or supplementary initiation flow beyond generic upload.
  - **Evidence**:
    - File validation constraints: `server/app/services/validation_service.py:5-39`
    - Version cap and overwrite behavior: `server/app/services/file_service.py:55-66`
    - SHA-256 + duplicate detection: `server/app/services/file_service.py:87-116`
    - Applicant ownership check: `server/app/services/file_service.py:44-49`
    - Frontend manual inputs: `client/src/features/files/FileUploadPage.vue:5-7`

- **Reviewers: state machine workflow + batch review ≤50 + comments/logs**
  - **Conclusion: Partial Pass**
  - **Rationale**:
    - FSM transitions and batch limit are implemented.
    - Review “comments” exist only as a `reason` field used for rejected transitions; there is no separate review comment model for approved transitions (prompt asks “filling in review comments”).
    - Traceable workflow history endpoint exists and includes correlation_id.
  - **Evidence**:
    - Transition matrix: `server/app/core/state_machine.py:14-35`
    - Batch review limit: `server/app/api/v1/routers/workflow.py:45-86`
    - History endpoint: `server/app/api/v1/routers/workflow.py:89-116`

- **Financial admins: income/expense, invoice attachments, stats, overspend confirmation**
  - **Conclusion: Partial Pass**
  - **Rationale**:
    - Transactions are recorded; invoice upload endpoint exists; overspend warning requires `confirm_overspend` true if >110% budget.
    - “Generate statistics by category and time” is not evidenced in these reviewed files; metrics snapshots exist but category/time breakdown for finance is not clearly present here.
  - **Evidence**:
    - Overspend confirmation logic: `server/app/services/finance_service.py:83-87`
    - Invoice upload: `server/app/api/v1/routers/finance.py:60-129`
    - Metric snapshot model exists: `server/app/models/models.py:159-166`
    - Frontend modal confirmation: `client/src/features/finance/FinancePage.vue:24-31`, `client/src/features/finance/FinancePage.vue:62-78`
  - **Manual verification note**: confirm any “stats by category/time” endpoints and UI beyond the finance page shown.

- **System: offline Postgres + local disk files + reserved similarity disabled**
  - **Conclusion: Pass**
  - **Rationale**: Backend requires PostgreSQL URL; uploads go to local `uploads/`; similarity endpoint returns disabled.
  - **Evidence**: `server/app/db/session.py:5-10`, `server/app/services/file_service.py:17-26`, `server/app/api/v1/routers/system.py:22-25`

- **Security requirements: hashing/salting, masking, lockout, auditing, encrypted config, backups**
  - **Conclusion: Partial Pass**
  - **Rationale**:
    - Passwords are hashed with bcrypt via passlib; lockout policy present (≥10 fails within 5 min → 30 min lock); masking logic present in application listing; audit log table is append-only.
    - Some security design issues exist (see Issues), and documentation/compose includes hardcoded secrets.
  - **Evidence**:
    - Password hashing: `server/app/core/security.py:6-23`
    - Lockout logic: `server/app/services/auth_service.py:57-71`
    - Role-based masking: `server/app/api/v1/routers/applications.py:54-62`
    - Append-only log enforcement: `server/app/main.py:20-34`, `server/app/models/models.py:228-234`
    - Encrypted config: `server/app/core/crypto_config.py:5-18`, `server/app/services/config_service.py:10-25`
    - Backups + restore: `server/app/services/backup_service.py:35-57`, `server/app/api/v1/routers/system.py:104-112`

### 5.2 End-to-end deliverable (2.2)

- **Conclusion: Pass (backend), Partial Pass (full-stack)**
- **Rationale**: Backend contains coherent models/routers/services/tests. Frontend exists and has basic flows and one E2E test, but core applicant UX is simplified compared to Prompt.
- **Evidence**: `server/app/main.py:67-86`, `server/tests/test_rules.py:22-269`, `client/tests/app.spec.ts:12-53`

---

## 6. Engineering and Architecture Quality

### 6.1 Structure / module decomposition (3.1)

- **Conclusion: Pass**
- **Rationale**: Backend is separated into routers/services/repositories/core/middleware; clear responsibilities. Frontend uses feature/page/service/store separation.
- **Evidence**: `server/app/main.py:4-16`, `server/app/api/v1/routers/*.py` (e.g. `server/app/api/v1/routers/workflow.py:1-12`), `client/src/features/**` (e.g. `client/src/features/finance/FinancePage.vue:35-57`)

### 6.2 Maintainability / extensibility (3.2)

- **Conclusion: Partial Pass**
- **Rationale**: Positive: policy engine and FSM matrix are centralized; idempotency and UoW patterns exist. Risks: schema management uses `Base.metadata.create_all()` at startup rather than migrations (could drift in real deployments); some commits occur inside auth dependency.
- **Evidence**: `server/app/main.py:36-60`, `server/tests/core/test_lifecycle.py:16-18`, `server/app/api/v1/deps.py:36-49`

---

## 7. Engineering Details and Professionalism

### 7.1 Error handling / logging / validation / API design (4.1)

- **Conclusion: Partial Pass**
- **Rationale**:
  - Good: validation on files and labels, explicit 409 conflicts, audit + endpoint observability, idempotency keys on critical endpoints.
  - Gaps: observability error logging drops exception details; some endpoints accept overly-generic payloads (e.g. materials label uses `payload: dict`); commit behavior inside dependencies may surprise.
- **Evidence**:
  - File validation: `server/app/services/validation_service.py:22-27`, `server/app/services/file_service.py:96-102`
  - Explicit conflict: `server/app/services/file_service.py:143-145`, `server/app/services/finance_service.py:63-65`
  - Observability logging: `server/app/middleware/observability.py:41-42`
  - Generic dict payload: `server/app/api/v1/routers/materials.py:48-64`

### 7.2 Product-like organization vs demo (4.2)

- **Conclusion: Partial Pass**
- **Rationale**: Backend reads as product-like with RBAC, audit, backups, metrics jobs. Frontend appears closer to a functional demo for core pages rather than the Prompt’s guided applicant checklist wizard.
- **Evidence**: `server/app/main.py:54-60`, `client/src/features/files/FileUploadPage.vue:5-7`

---

## 8. Prompt Understanding and Requirement Fit (5.1)

- **Conclusion: Partial Pass**
- **Rationale**: Many backend semantics match the Prompt precisely (lockout policy, SHA-256 fingerprint, disabled similarity endpoint, overspend secondary confirmation, batch limit, append-only logs). The largest mismatch is the applicant-facing flow implementation/UI and checklist semantics.
- **Evidence**:
  - Lockout: `server/app/services/auth_service.py:57-71`
  - SHA-256 + duplicate: `server/app/services/file_service.py:87-116`
  - Disabled similarity: `server/app/api/v1/routers/system.py:22-25`
  - Overspend confirmation: `server/app/services/finance_service.py:83-87`
  - Batch limit: `server/app/api/v1/routers/workflow.py:45-49`
  - Frontend manual upload flow: `client/src/features/files/FileUploadPage.vue:5-7`

---

## 9. Aesthetics (frontend-only / full-stack) (6.1)

- **Conclusion: Cannot Confirm Statistically**
- **Rationale**: Visual quality, spacing, and interaction feedback require running the UI. Static code shows components like modals/steppers/tables exist, but rendering quality cannot be asserted.
- **Evidence**: `client/src/features/applications/ApplicationWizardPage.vue:1-33`, `client/src/features/finance/FinancePage.vue:24-31`
- **Manual verification note**: run UI and verify hierarchy/spacing/consistency and scenario fit.

---

## 10. Issues / Suggestions (Severity-Rated)

### Blocker

1) **Hardcoded secrets and weak defaults in deployment manifests**
   - **Conclusion**: Fail (security hardening)
   - **Evidence**: `docker-compose.yml:24-28` (e.g. `JWT_SECRET: super-secret-change-me`, `ENCRYPTION_KEY: change-me-too`), `docker-compose.yml:7-10` (default DB password)
   - **Impact**: If used as-is, deployments are trivially compromised; violates “professional software practice” and the Prompt’s security posture.
   - **Minimum actionable fix**: Remove hardcoded secrets; require values via environment or `.env.example`; add validation that rejects default placeholders at startup.

### High

2) **Frontend deviates from Prompt’s core applicant flows (checklist-driven, item-by-item, labeled statuses, lock after deadline, supplementary initiation)**
   - **Conclusion**: Partial Pass → likely fail for “prompt fit” depending on strictness
   - **Evidence**: `client/src/features/files/FileUploadPage.vue:5-7` (manual Application ID + Material Type), `client/src/features/files/FileUploadPage.vue:44-55` (checklist fetched but not integrated), `client/src/features/applications/ApplicationWizardPage.vue:58-69` (“minimal compatible subset” comment + only title/deadline used)
   - **Impact**: Applicants cannot follow the described guided checklist process; key business semantics are missing/unclear in UI.
   - **Minimum actionable fix**: Implement checklist selection per application; display per-item status labels; enforce/reflect deadline lock and 72h supplementary flow with reason capture; show version history per checklist item.

3) **Logout endpoint allows revocation of arbitrary token parameter and leaks token subject**
   - **Conclusion**: Fail (auth API design)
   - **Evidence**: `server/app/api/v1/routers/auth.py:40-43` (logout takes `token: str` separate from authenticated bearer, then returns decoded `sub`)
   - **Impact**: A logged-in user could submit someone else’s token string (if obtained) to revoke it; response echoes token subject; muddles security boundary.
   - **Minimum actionable fix**: Derive logout target from the authenticated bearer token only; do not decode/echo arbitrary token subject; accept no token parameter.

4) **Checklist integrity can be bypassed by creating new checklist items on upload**
   - **Conclusion**: Fail (business rule enforcement)
   - **Evidence**: `server/app/api/v1/routers/files.py:22-26` (non-digit `material_type` → `get_or_create`)
   - **Impact**: Applicants (or any uploader role) can invent new material types not in the predefined checklist, undermining “upload materials item by item according to the checklist.”
   - **Minimum actionable fix**: Require `checklist_item_id` referencing existing checklist items; restrict checklist management to admins; validate material type against application’s checklist.

### Medium

5) **Schema lifecycle relies on `create_all()` at runtime; migrations not evidenced as the source of truth**
   - **Conclusion**: Partial Pass (deployment robustness risk)
   - **Evidence**: `server/app/main.py:38-39`
   - **Impact**: Production schema drift risk; “create_all” does not handle migrations reliably (constraints/index changes).
   - **Minimum actionable fix**: Use Alembic migrations as the canonical schema lifecycle; remove/disable `create_all()` in production mode.

6) **Authorization dependency commits DB session during permission check**
   - **Conclusion**: Partial Pass (transactionality risk)
   - **Evidence**: `server/app/api/v1/deps.py:36-49`
   - **Impact**: Commits can occur outside business Unit-of-Work boundaries; could accidentally commit other pending changes in the same session.
   - **Minimum actionable fix**: Use a separate session for audit logging or ensure permission checks never share a session with mutable business state; avoid committing in dependency.

7) **Observability middleware logs errors without exception context**
   - **Conclusion**: Partial Pass (troubleshooting gap)
   - **Evidence**: `server/app/middleware/observability.py:41-42`
   - **Impact**: Failures in observability write path are hard to diagnose; may silently lose monitoring data.
   - **Minimum actionable fix**: Include exception details in log (`logger.exception`) and/or structured error fields.

### Low

8) **Deliverable includes prebuilt frontend artifacts while also having source (potential duplication/confusion)**
   - **Conclusion**: Partial Pass (packaging hygiene)
   - **Evidence**: `client/dist/index.html:1-13`, plus `.gitignore` suggests these are intended to be ignored: `.gitignore:5`
   - **Impact**: Increases repo size; risks stale build being mistaken for authoritative; harder audit.
   - **Minimum actionable fix**: Remove `client/dist` from source delivery or clearly document it as an optional artifact with reproducible build steps.

9) **Deliverable contains a Python virtual environment directory (packaging hygiene)**
   - **Conclusion**: Partial Pass (packaging hygiene)
   - **Evidence**: `.venv/pyvenv.cfg:1-6`, and it is intended to be ignored: `.gitignore:1`
   - **Impact**: Bloats delivery; can contain platform-specific binaries; raises supply-chain review burden.
   - **Minimum actionable fix**: Exclude `.venv` from delivery; rely on `server/requirements.txt` (`server/requirements.txt:1-14`).

---

## 11. Security Review Summary

- **Authentication entry points**
  - **Conclusion: Partial Pass**
  - **Evidence**: `server/app/api/v1/routers/auth.py:16-51`, `server/app/services/auth_service.py:52-86`
  - **Reasoning**: Strong password hashing and lockout exist; logout design issue noted (High).

- **Route-level authorization**
  - **Conclusion: Pass (mostly)**
  - **Evidence**: `server/app/api/v1/deps.py:29-51` used across routers (e.g. `server/app/api/v1/routers/files.py:19-21`, `server/app/api/v1/routers/finance.py:18-40`)

- **Object-level authorization**
  - **Conclusion: Partial Pass**
  - **Evidence**: Applicant ownership check on upload: `server/app/services/file_service.py:47-49`; materials list check: `server/app/api/v1/routers/materials.py:18-21`
  - **Reasoning**: Applicant isolation appears implemented for some endpoints; needs systematic verification across all resources/routes (manual verification recommended).

- **Function-level authorization**
  - **Conclusion: Pass**
  - **Evidence**: Permission policy checks: `server/app/core/policy_engine.py:3-19`, enforcement: `server/app/api/v1/deps.py:29-51`

- **Tenant / user data isolation**
  - **Conclusion: Cannot Confirm Statistically**
  - **Evidence**: No explicit tenant model found in reviewed models (`server/app/models/models.py:7-226`)
  - **Reasoning**: Prompt does not explicitly require multi-tenant; but “permission isolation” and “data scope” imply careful data partitioning. Current implementation appears single-instance, role-based.

- **Admin / internal / debug endpoint protection**
  - **Conclusion: Partial Pass**
  - **Evidence**: System endpoints require `system:admin`: `server/app/api/v1/routers/system.py:22-112`, but secrets are exposed in plaintext to admins: `server/app/services/config_service.py:20-25`
  - **Reasoning**: Protected by RBAC, but “get secret” returns decrypted value; acceptable only if explicitly intended and audited.

---

## 12. Tests and Logging Review

- **Unit tests**
  - **Conclusion: Partial Pass**
  - **Evidence**: Tests are primarily API-level with FastAPI `TestClient`: `server/tests/test_rules.py:4-9`
  - **Reasoning**: Behavior is tested, but few pure unit tests; still valuable coverage.

- **API / integration tests**
  - **Conclusion: Pass**
  - **Evidence**: `server/tests/test_rules.py:22-269`, `server/tests/test_reliability_properties.py:31-92`

- **Logging categories / observability**
  - **Conclusion: Partial Pass**
  - **Evidence**: Audit logs: `server/app/services/audit_service.py:9-33`; observability writes: `server/app/middleware/observability.py:18-43`

- **Sensitive-data leakage risk in logs / responses**
  - **Conclusion: Partial Pass**
  - **Evidence**: Logout echoes decoded subject: `server/app/api/v1/routers/auth.py:40-43`; system secret endpoint returns decrypted value: `server/app/services/config_service.py:20-25`
  - **Reasoning**: Both are gated but still raise exposure risk; should be reviewed for least-privilege.

---

## 13. Test Coverage Assessment (Static Audit)

### 13.1 Test Overview

- **Backend framework**: `pytest` + FastAPI `TestClient`
  - **Evidence**: `server/requirements.txt:9-10`, `server/tests/test_rules.py:4-9`
- **Frontend framework**: Playwright E2E
  - **Evidence**: `client/package.json:6-11`, `client/playwright.config.ts:1-13`, `client/tests/app.spec.ts:1-53`
- **Test entry points**
  - Backend: `pytest` implied; lifecycle fixtures: `server/tests/conftest.py:1-16`
  - Frontend: `npm run test:e2e`: `client/package.json:6-11`
- **Documentation provides test commands**
  - **Evidence**: `README.md:67-85`

### 13.2 Coverage Mapping Table

| Requirement / Risk Point | Mapped Test Case(s) | Key Assertion / Fixture / Mock | Coverage | Gap | Minimum Test Addition |
|---|---|---|---|---|---|
| RBAC: applicant cannot approve workflow | `server/tests/test_rules.py:22-31` | 403 for applicant, 200 for reviewer | **basically covered** | None obvious | Add negative tests for finance/system endpoints by wrong roles |
| FSM transition validation + reason required for reject | `server/tests/test_rules.py:33-40`, `server/tests/test_reliability_properties.py:31-59` | invalid transitions rejected, reason required | **basically covered** | Limited state coverage depth | Add table-driven tests for each transition in matrix |
| Concurrency / optimistic version control | `server/tests/test_rules.py:42-51`, `server/tests/test_rules.py:119-136` | 409 on version mismatch; only one winner in race | **sufficient** | None obvious | Add similar race tests for materials label changes |
| File upload type + MIME + size limits | `server/tests/test_rules.py:174-200` | sha256 match; bad mime 400; oversize 400 | **sufficient** | Total 200MB limit not directly tested | Add test that accumulates total >200MB and asserts 400 |
| File versioning (≤3) and label transitions | (No direct test for cap=3) | — | **insufficient** | Cap/rotation behavior not covered | Add test uploading 4 times and assert only 3 versions exist and version numbers rotate |
| Duplicate SHA-256 rejection | `server/tests/test_rules.py:53-70` | second upload returns 409 | **sufficient** | None | — |
| Deadline lock + 72h supplementary once with reason | `server/tests/test_rules.py:72-90` | second supplementary denied 400 | **basically covered** | Not testing “>72h expired” branch | Add test where deadline is >72h in past and assert 400 |
| Finance overspend requires secondary confirmation | `server/tests/test_rules.py:92-105` | `requires_confirmation` then accept | **sufficient** | None | Add test that income txn doesn’t require confirm (if supported) |
| Budget locked after transactions | `server/tests/test_rules.py:92-105` | budget update returns 409 | **basically covered** | None | — |
| Object-level isolation (applicant sees own apps/txns) | `server/tests/test_rules.py:202-219` | applicant list excludes other’s app; tx list filtered | **basically covered** | No test for materials list isolation | Add test that applicant cannot list materials/history for other’s application |
| Batch review ≤50 + partial success response | `server/tests/test_rules.py:221-238` | 51 rejected; partial returns 200/207 | **basically covered** | None | Add test for 207 structure integrity |
| Frontend core flow (register/login/upload/review/history) | `client/tests/app.spec.ts:12-53` | UI and API assertions | **basically covered** | Doesn’t cover checklist UI, label states, deadline lock UI | Add E2E tests for checklist selection and label display if implemented |

### 13.3 Security Coverage Audit

- **Authentication**: **basically covered**
  - **Evidence**: login/register used in tests: `server/tests/utils/bootstrap.py:16-39`, `client/tests/app.spec.ts:15-19`
  - **Gap**: no explicit tests for lockout timing and 423 response.
  - **Minimum test addition**: simulate ≥10 failed logins in 5 minutes and assert 423.

- **Route authorization**: **basically covered**
  - **Evidence**: `server/tests/test_rules.py:22-31`
  - **Gap**: system admin endpoints not tested for non-admin denial.
  - **Minimum test addition**: attempt `/api/v1/system/export` with reviewer and assert 403.

- **Object-level authorization**: **insufficient**
  - **Evidence**: apps/finance filtering: `server/tests/test_rules.py:202-219`
  - **Gap**: materials/history/exports not comprehensively tested.
  - **Minimum test addition**: add tests for `/api/v1/materials` and `/api/v1/workflow/{id}/history` access control across roles.

- **Tenant / data isolation**: **not applicable / cannot confirm**
  - **Evidence**: no tenant model in reviewed code: `server/app/models/models.py:7-226`

- **Admin/internal protection**: **missing coverage**
  - **Evidence**: no tests targeting `/api/v1/system/*` protections found in reviewed tests.
  - **Minimum test addition**: verify 403 for non-admin, and expected behavior for admin for each critical endpoint.

### 13.4 Final Coverage Judgment

- **Conclusion: Partial Pass**
  - **Reasoning**: Core backend workflows have meaningful tests (RBAC, FSM, idempotency, concurrency, file constraints, finance overspend). However, notable gaps remain in object-level authorization breadth and system/admin endpoint protection tests; frontend tests cover only a thin slice and do not validate Prompt-specific applicant UX requirements.

---

## 14. Final Notes

- This audit is static-only and does not assert runtime success.
- The backend is closer to Prompt-complete than the frontend; the largest acceptance risk is **prompt-to-UI fit** and **deployment security defaults**.
