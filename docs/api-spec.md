
# Activity Registration and Funding Audit Management Platform API Specification

**Project Name:** Activity Registration and Funding Audit Management Platform  
**Version:** 1.0.0  
**Date:** April 2026  
**Status:** Backend Implementation Reference  

## Overview

This document reflects the **actual implemented FastAPI endpoints** for the platform. It serves as the living API contract between the frontend and backend.

- **Base URL (API):** `/api/v1`
- **Health Check (non-API):** `/health`
- **Authorization:** JWT Bearer token for protected endpoints (`Authorization: Bearer <access_token>`)
- **ID Type:** Integer in database, returned as JSON number
- **Pagination:** `page` + `size` (server enforces `size <= 100` on paginated list endpoints)
- **Correlation ID:** `X-Correlation-ID` request header is accepted; server generates one if missing and echoes it back in the response header
- **Idempotency:** `Idempotency-Key` header is **required** for selected mutating endpoints (see “Idempotency”)
- **Permissions:** Enforced via `require_permission("<permission>")`

---

## Authentication & Authorization

### Token format

- **Access tokens** are JWTs with `typ = "access"`.
- **Refresh tokens** are JWTs with `typ = "refresh"` and are rotated on use.

### Auth header

```http
Authorization: Bearer <access_token>
```

### Role model (implemented)

| Role | Notes |
|---|---|
| `applicant` | Default role for self-registered users (when enabled). |
| `reviewer` | Reviews and transitions applications. |
| `financial_admin` | Sets budgets, records transactions, and reads metrics. |
| `system_admin` | Full access (`"*"`). |

### Permission model (implemented)

| Role | Permissions (sorted) |
|---|---|
| `applicant` | `application:create`, `application:read`, `file:upload` |
| `reviewer` | `application:read`, `review:list`, `workflow:transition` |
| `financial_admin` | `application:read`, `finance:budget`, `finance:transaction`, `metrics:read` |
| `system_admin` | `*` |

### Public registration toggle

`POST /api/v1/auth/register` exists but returns **404** unless environment variable `ENABLE_PUBLIC_REGISTRATION` is set to a truthy value (`1`, `true`, `yes`).

---

## Common Headers

| Header | Required | Description |
|---|---:|---|
| `Authorization` | Conditional | Required for protected endpoints. Format: `Bearer <access_token>`. |
| `X-Correlation-ID` | No | If omitted, server generates a UUID. Echoed back in response headers. |
| `Idempotency-Key` | Conditional | Required for selected mutating endpoints (see below). |

---

## Idempotency

The server requires `Idempotency-Key` for `POST`, `PUT`, or `PATCH` requests where the request path starts with one of:

| Path prefix | Typical operations |
|---|---|
| `/api/v1/files/upload` | File/material uploads |
| `/api/v1/workflow/` | Workflow transitions and batch review |
| `/api/v1/finance/transactions` | Finance transaction recording |
| `/api/v1/finance/budget` | Budget set/update |

If `Idempotency-Key` is missing for these requests, the server returns:

```json
{ "detail": "Idempotency-Key header required" }
```

---

## Error Handling

Most endpoints use FastAPI’s standard error structure:

| Status | Shape |
|---:|---|
| `4xx/5xx` | `{"detail": "<message>"}` |

One endpoint returns a structured validation error payload as the `detail` value:

- `POST /api/v1/forms/application/validate` on failure: `{"detail": {"errors": [...]}}`

---

## Endpoints Summary

### Health

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `GET` | `/health` | No | — | Liveness check. |

---

### Auth (`/auth`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | No | — | Create an applicant user **only if** public registration is enabled; otherwise returns `404`. |
| `POST` | `/api/v1/auth/login` | No | — | Login and receive `access_token` and `refresh_token`. |
| `POST` | `/api/v1/auth/refresh` | No | — | Rotate refresh token and issue new access token. |
| `POST` | `/api/v1/auth/logout` | Yes | (token-based) | Revoke an access token by its `jti`. |
| `GET` | `/api/v1/auth/me` | Yes | (token-based) | Return current username, role, and permissions. |

#### `POST /api/v1/auth/register`

- **Notes:** Returns `404` unless `ENABLE_PUBLIC_REGISTRATION` is truthy.
- **Request body:**

```json
{
  "username": "alice",
  "password": "p@ssw0rd",
  "id_number": "ID-12345",
  "phone_number": "+1-555-0100",
  "email": "alice@example.com"
}
```

- **Response (200):**

```json
{ "message": "User created" }
```

#### `POST /api/v1/auth/login`

- **Request body:**

```json
{
  "username": "alice",
  "password": "p@ssw0rd"
}
```

- **Response (200):**

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

- **Error cases (implemented):**
  - `401`: `{"detail":"Invalid credentials"}`
  - `423`: `{"detail":"Account locked for 30 minutes"}`

#### `POST /api/v1/auth/refresh`

- **Request body:**

```json
{ "refresh_token": "<jwt>" }
```

- **Response (200):**

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

- **Error cases (implemented):**
  - `401`: invalid token type, token not found, token reuse detected, etc.

#### `POST /api/v1/auth/logout`

- **Auth:** Bearer access token is required (via dependency).
- **Input:** `token` is a **query parameter** (the token to revoke).

Example:

```http
POST /api/v1/auth/logout?token=<access_jwt>
Authorization: Bearer <access_jwt>
```

- **Response (200):**

```json
{
  "status": "ok",
  "subject": "alice",
  "by": "alice"
}
```

#### `GET /api/v1/auth/me`

- **Response (200):**

```json
{
  "username": "alice",
  "role": "applicant",
  "permissions": ["application:create", "application:read", "file:upload"]
}
```

---

### Applications (`/applications`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/applications` | Yes | `application:create` | Create an application. |
| `GET` | `/api/v1/applications` | Yes | `application:read` | List applications with filtering/sorting/pagination; visibility depends on role. |

#### `POST /api/v1/applications`

- **Request body:**

```json
{
  "title": "Community Sports Grant",
  "deadline": "2026-05-01T00:00:00Z"
}
```

- **Response (200):**

```json
{ "id": 1, "status": "Submitted", "version": 1 }
```

#### `GET /api/v1/applications`

- **Query parameters:**

| Name | Type | Default | Notes |
|---|---|---:|---|
| `status` | string | — | Optional status filter. |
| `sort_by` | string | `id` | Unknown values fall back to `id`. |
| `sort_dir` | string | `asc` | Use `desc` for descending. |
| `page` | int | `1` | 1-based page index. |
| `size` | int | `20` | Server caps at `100`. |

- **Response (200):**

```json
{
  "total": 1,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 1,
      "title": "Community Sports Grant",
      "status": "Submitted",
      "version": 1,
      "owner_masked": "********2345",
      "owner_contact": {
        "id_number": "********2345",
        "phone_number": "**********00",
        "email": "a***@example.com"
      }
    }
  ],
  "viewer": "alice"
}
```

- **Privacy note (implemented):** Owner contact fields are masked depending on the viewer’s role.

---

### Workflow (`/workflow`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/workflow/{application_id}/transition` | Yes | `workflow:transition` | Transition an application between workflow states (optimistic version check). |
| `GET` | `/api/v1/workflow/reviews` | Yes | `review:list` | List applications for review (paginated). |
| `POST` | `/api/v1/workflow/batch-review` | Yes | `workflow:transition` | Batch transitions (max 50 items). Returns `200`, `207`, or `400` depending on outcomes. |
| `GET` | `/api/v1/workflow/{application_id}/history` | Yes | `review:list` | Application transition history (with applicant access restriction). |

#### `POST /api/v1/workflow/{application_id}/transition`

- **Idempotency:** `Idempotency-Key` required.
- **Request body:**

```json
{
  "to_state": "Approved",
  "reason": "Meets all requirements",
  "expected_version": 1
}
```

- **Response (200):**

```json
{ "status": "Approved", "version": 2 }
```

- **Error cases (implemented):**
  - `404`: application not found
  - `409`: version mismatch (`"Version mismatch, reload application"`)
  - `400`: invalid transition (`detail` is a string error from FSM validation)

#### `GET /api/v1/workflow/reviews`

- **Query parameters:** `status`, `sort_by`, `sort_dir`, `page`, `size` (same semantics as applications list; `size` capped at 100).
- **Response (200):**

```json
{
  "total": 1,
  "items": [{ "id": 1, "status": "Submitted", "version": 1 }],
  "reviewer": "reviewer1"
}
```

#### `POST /api/v1/workflow/batch-review`

- **Idempotency:** `Idempotency-Key` required (the server appends `-<application_id>` for each item internally).
- **Request body:** list of objects (max 50)

```json
[
  { "application_id": 1, "to_state": "Approved", "expected_version": 1, "reason": "OK" },
  { "application_id": 2, "to_state": "Supplemented", "expected_version": 3 }
]
```

- **Response:**
  - `200` when all items succeed
  - `207` when partial success
  - `400` when none succeed or batch size > 50

Example success (200/207/400 content shape):

```json
{
  "count": 2,
  "results": [
    { "item_id": 1, "status": "ok", "result": { "status": "Approved", "version": 2 } },
    { "item_id": 2, "status": "failed", "error_code": "VERSION_CONFLICT", "message": "Version conflict" }
  ]
}
```

#### `GET /api/v1/workflow/{application_id}/history`

- **Response (200):**

```json
{
  "application_id": 1,
  "items": [
    {
      "from_state": "Submitted",
      "to_state": "Approved",
      "actor": 5,
      "timestamp": "2026-04-13T12:34:56.789012",
      "reason": "OK",
      "correlation_id": "c3f6b2b3-..."
    }
  ]
}
```

- **Access rule (implemented):** Applicants may only access history for their own applications; otherwise `403`.

---

### Files (`/files`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/files/upload` | Yes | `file:upload` | Upload a material file (creates/updates a checklist item if needed). |

#### `POST /api/v1/files/upload`

- **Status:** Implemented (upload only).
- **Idempotency:** `Idempotency-Key` required.
- **Content-Type:** `multipart/form-data`
- **Form fields (implemented):**

| Field | Type | Required | Notes |
|---|---|---:|---|
| `application_id` | int | Yes | Target application. |
| `material_type` | string | Yes | If numeric, treated as a checklist item ID; otherwise treated as a checklist code to `get_or_create`. |
| `label` | string | No | Default: `"Submitted"`. |
| `correction_reason` | string \| null | No | Used for submission window validation. |
| `file` | file | Yes | Uploaded content. |

- **Response (200):**

```json
{ "status": "ok", "version": 1, "sha256": "<hex>" }
```

- **Notable error cases (implemented):**
  - `400`: file metadata invalid; invalid filename; size limits exceeded
  - `403`: applicant uploading to someone else’s application
  - `404`: application not found
  - `409`: duplicate material detected; concurrent upload conflict

#### Planned / Partial (not implemented)

The following file endpoints are **not present** in the current backend router and are therefore **not available** yet:

| Capability | Status |
|---|---|
| Download material content | Planned (no endpoint implemented) |
| List files / versions directly under `/files` | Planned (use `/materials` instead) |
| Delete file/material versions | Planned (no endpoint implemented) |

---

### Materials (`/materials`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/materials` | Yes | `application:read` | List materials and versions for an application (with applicant ownership check). |
| `POST` | `/api/v1/materials/{material_id}/label` | Yes | `review:list` | Set the latest material version label (role-validated transition). |

#### `GET /api/v1/materials`

- **Query parameters:**

| Name | Type | Required |
|---|---|---:|
| `application_id` | int | Yes |

- **Response (200):**

```json
{
  "application_id": 1,
  "items": [
    {
      "material_id": 10,
      "checklist_item": { "id": 3, "code": "ID_DOC", "name": "Identity Document" },
      "versions": [
        {
          "version": 1,
          "label": "Submitted",
          "correction_reason": null,
          "sha256": "<hex>",
          "size": 12345,
          "uploaded_at": "2026-04-13T12:34:56.789012"
        }
      ]
    }
  ]
}
```

- **Access rule (implemented):** Applicants may only list materials for their own applications; otherwise `403`.

#### `POST /api/v1/materials/{material_id}/label`

- **Request body:** (dynamic payload)

```json
{ "label": "Needs Correction", "correction_reason": "Missing signature" }
```

- **Response (200):**

```json
{ "status": "ok", "material_id": 10, "label": "Needs Correction" }
```

- **Error cases (implemented):**
  - `400`: `label required` or invalid label transition for role
  - `404`: material not found

---

### Checklists (`/checklists`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/checklists/items` | Yes | `application:read` | List checklist items. |

#### `GET /api/v1/checklists/items`

- **Response (200):**

```json
{
  "items": [
    { "id": 1, "code": "ID_DOC", "name": "Identity Document" }
  ]
}
```

---

### Finance (`/finance`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/finance/budget` | Yes | `finance:budget` | Create/update an application budget (locked once transactions exist). |
| `POST` | `/api/v1/finance/transactions` | Yes | `finance:transaction` | Record a transaction; may require overspend confirmation. |
| `GET` | `/api/v1/finance/transactions` | Yes | `finance:transaction` | List transactions (paginated). |
| `POST` | `/api/v1/finance/transactions/{transaction_id}/invoice` | Yes | `finance:transaction` | Upload an invoice attachment for a transaction. |

#### `POST /api/v1/finance/budget`

- **Idempotency:** `Idempotency-Key` required.
- **Request body:**

```json
{ "application_id": 1, "total_budget": 10000.0 }
```

- **Response (200):**

```json
{ "status": "ok", "version": 1 }
```

- **Error cases (implemented):**
  - `409`: budget locked after transaction activity; concurrent finance conflict

#### `POST /api/v1/finance/transactions`

- **Idempotency:** `Idempotency-Key` required.
- **Request body:**

```json
{
  "application_id": 1,
  "type": "expense",
  "amount": 250.0,
  "invoice_path": null,
  "confirm_overspend": false
}
```

- **Response (200) — recorded:**

```json
{ "status": "recorded", "requires_confirmation": false }
```

- **Response (200) — requires secondary confirmation (implemented as a normal 200 response):**

```json
{ "warning": "Secondary confirmation required", "requires_confirmation": true }
```

- **Error cases (implemented):**
  - `400`: budget not set; amount must be positive

#### `GET /api/v1/finance/transactions`

- **Query parameters:**

| Name | Type | Default | Notes |
|---|---|---:|---|
| `application_id` | int | — | Optional filter. |
| `txn_type` | string | — | Optional filter (e.g., `income`, `expense`). |
| `sort_by` | string | `id` | Repository-dependent sort field. |
| `sort_dir` | string | `asc` | Use `desc` for descending. |
| `page` | int | `1` | 1-based page index. |
| `size` | int | `20` | Server caps at `100`. |

- **Response (200):**

```json
{
  "total": 1,
  "page": 1,
  "size": 20,
  "items": [
    { "id": 1, "application_id": 1, "type": "expense", "amount": 250.0 }
  ],
  "viewer": "finadmin1"
}
```

#### `POST /api/v1/finance/transactions/{transaction_id}/invoice`

- **Content-Type:** `multipart/form-data`
- **Form fields:**

| Field | Type | Required |
|---|---|---:|
| `file` | file | Yes |

- **Response (200):**

```json
{ "status": "ok", "transaction_id": 1, "sha256": "<hex>" }
```

- **Access rule (implemented):** Applicants may only upload invoices for transactions on their own applications; otherwise `403`.

- **Notable error cases (implemented):**
  - `404`: transaction not found; application not found
  - `400`: invalid filename; file metadata invalid; file exceeds 20MB

---

### Metrics (`/metrics`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/metrics/latest` | Yes | `metrics:read` | Return latest snapshot if present; otherwise compute current rates and return them. |

#### `GET /api/v1/metrics/latest`

- **Response (200):**

```json
{
  "snapshot_date": "2026-04-13T00:10:00+00:00",
  "approval_rate": 0.5,
  "correction_rate": 0.25,
  "overspending_rate": 0.0
}
```

- **Notes (implemented):**
  - If no snapshot exists, the response omits `snapshot_date` and returns computed rates:

```json
{
  "approval_rate": 0.5,
  "correction_rate": 0.25,
  "overspending_rate": 0.0
}
```

---

### Forms (`/forms`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/forms/application` | Yes | `application:create` | Return the application form definition. |
| `POST` | `/api/v1/forms/application/validate` | Yes | `application:create` | Validate an application payload; returns 400 with structured errors on failure. |

#### `GET /api/v1/forms/application`

- **Response (200):** A JSON form definition produced by `get_application_form_definition()`.

#### `POST /api/v1/forms/application/validate`

- **Request body:** arbitrary JSON payload

```json
{ "any": "shape" }
```

- **Response (200):**

```json
{ "status": "ok" }
```

- **Response (400):**

```json
{
  "detail": {
    "errors": [
      { "field": "title", "message": "Required" }
    ]
  }
}
```

---

### System (`/system`)

| Method | Path | Auth | Permission | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/system/duplicate-check` | Yes | `system:admin` | Reserved endpoint; currently returns static disabled response. |
| `GET` | `/api/v1/system/export` | Yes | `system:admin` | Create a CSV export; returns a `download_id`. |
| `GET` | `/api/v1/system/export/{download_id}` | Yes | `system:admin` | Download a generated CSV export. |
| `POST` | `/api/v1/system/users` | Yes | `system:admin` | Provision a user with a specified role. |
| `POST` | `/api/v1/system/config/secret` | Yes | `system:admin` | Set a secret key/value. |
| `GET` | `/api/v1/system/config/secret/{key}` | Yes | `system:admin` | Get a secret by key. |
| `POST` | `/api/v1/system/recovery/backup` | Yes | `system:admin` | Create a backup immediately. |
| `POST` | `/api/v1/system/recovery/restore` | Yes | `system:admin` | Restore from a provided backup path. |

#### `GET /api/v1/system/duplicate-check`

- **Response (200):**

```json
{ "enabled": false, "note": "Reserved endpoint for local similarity/duplicate checks" }
```

#### `GET /api/v1/system/export`

- **Query parameters:**

| Name | Type | Required | Allowed values |
|---|---|---:|---|
| `report_type` | string | Yes | `audit`, `finance`, `compliance`, `whitelist` |

- **Response (200):**

```json
{ "download_id": "<hex>" }
```

#### `GET /api/v1/system/export/{download_id}`

- **Response (200):** File download (`text/csv`).

#### `POST /api/v1/system/users`

- **Request body:**

```json
{ "username": "reviewer1", "password": "p@ssw0rd", "role": "reviewer" }
```

- **Response (200):**

```json
{ "message": "User provisioned", "username": "reviewer1", "role": "reviewer" }
```

#### `POST /api/v1/system/config/secret`

- **Request body:**

```json
{ "key": "SOME_KEY", "value": "some-value" }
```

- **Response (200):** Secret record returned from `ConfigService.set_secret(...)`.

- **Error cases (implemented):**
  - `400`: `{"detail":"key and value required"}`

#### `GET /api/v1/system/config/secret/{key}`

- **Response (200):** Secret record returned from `ConfigService.get_secret(...)`.
- **Error cases (implemented):**
  - `404`: `{"detail":"Not found"}`

#### `POST /api/v1/system/recovery/backup`

- **Response (200):**

```json
{ "backup_path": "/path/to/backup", "by": "admin1" }
```

#### `POST /api/v1/system/recovery/restore`

- **Request body:**

```json
{ "backup_path": "/path/to/backup" }
```

- **Response (200):**

```json
{ "restored_db": true, "by": "admin1" }
```
