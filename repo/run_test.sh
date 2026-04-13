#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
export ENV="test"
export JWT_SECRET="test-secret"
export ENCRYPTION_KEY="test-key"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_db"
export BACKUP_DIR="/backups"
export EXPORT_DIR="/exports"
export BOOTSTRAP_SYSTEM_ADMIN_USERNAME="sysadmin"
export BOOTSTRAP_SYSTEM_ADMIN_PASSWORD="password"

cleanup() {
  docker compose -f "$ROOT_DIR/docker-compose.test.yml" down -v >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker compose -f "$ROOT_DIR/docker-compose.test.yml" up --build --abort-on-container-exit --exit-code-from client-test
