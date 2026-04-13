# Activity Registration and Funding Audit Management Platform

This repository contains a production-structured full-stack system for managing activity registration, review workflows, funding operations, and compliance tracking. It is designed for multi-role operation, deterministic workflow transitions, and auditable business actions.

The platform includes a Vue 3 frontend and a FastAPI backend running with PostgreSQL. The system is built for operational reliability and static verifiability, with strict role-based access controls, append-only audit behavior, and test automation for backend and frontend paths.

## Key Features

- Multi-role system (`applicant`, `reviewer`, `financial_admin`, `system_admin`)
- Workflow FSM with validated state transitions
- Binary-safe file upload and versioned material storage
- Finance workflows with budget checks and overspending confirmation logic
- Audit logging, endpoint observability, and metrics snapshot jobs

## Project Structure

- `client` -> Vue 3 frontend
- `server` -> FastAPI backend
- `docker-compose.yml`
- `run_test.sh`

## Environment Variables

The backend requires PostgreSQL and the following environment variables:

```env
DATABASE_URL=postgresql://user:password@db:5432/app_db
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_fernet_key
```

- **Public registration is disabled by default**. To enable it (not recommended for production), explicitly set:
  - `ENABLE_PUBLIC_REGISTRATION=true`

- `DATABASE_URL` is required (no SQLite fallback)
- Values must match your `docker-compose.yml` database service configuration

## Run the System

```bash
docker compose up --build
```

This command starts:

- frontend (`client`)
- backend (`server`)
- PostgreSQL (`db`)

Access points:

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)

## Database

- PostgreSQL is used as the primary database
- No SQLite fallback is supported
- Data is stored locally via Docker volumes

## Backup

- Backups are PostgreSQL-native (`pg_dump` / `pg_restore`)
- Backup files are stored in `/backups/`
- Timestamped backups are retained for the last 7 days

## Run Tests

```bash
chmod +x run_test.sh
./run_test.sh
```

This script runs:

- Backend tests (`pytest`)
- Frontend tests (Playwright)

## Playwright Setup

Use Node.js `>= 18.19`, then install browsers once:

```bash
npx playwright install
```

## Troubleshooting

- If Docker fails:
  - ensure Docker is running
- If frontend is not accessible:
  - check port `5173` is exposed
- If backend fails:
  - verify `DATABASE_URL` is set correctly
- If tests fail:
  - ensure Node.js `>= 18.19`
