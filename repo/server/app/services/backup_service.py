import os
import subprocess
from urllib.parse import urlparse, unquote
from datetime import datetime, timedelta
from pathlib import Path


BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/backups"))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _parse_database_url(database_url: str) -> tuple[str, str, str, int, str]:
    normalized = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    parsed = urlparse(normalized)
    if parsed.scheme != "postgresql":
        raise RuntimeError("DATABASE_URL must be postgresql://... for backups")
    host = parsed.hostname or "localhost"
    user = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    port = int(parsed.port or 5432)
    dbname = (parsed.path or "").lstrip("/")
    if not user or not dbname:
        raise RuntimeError("DATABASE_URL missing user or database name")
    return host, user, password, port, dbname


def _retention_cleanup(days: int = 7):
    threshold = datetime.utcnow() - timedelta(days=days)
    for file in BACKUP_DIR.glob("backup_*.dump"):
        ts = datetime.strptime(file.stem.replace("backup_", ""), "%Y%m%d_%H%M%S")
        if ts < threshold:
            file.unlink(missing_ok=True)


def create_backup() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for backups")
    host, user, password, port, dbname = _parse_database_url(database_url)
    target = BACKUP_DIR / f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.dump"
    env = {**os.environ, "PGPASSWORD": password} if password else os.environ.copy()
    subprocess.run(["pg_dump", "-Fc", "-h", host, "-p", str(port), "-U", user, "-f", str(target), dbname], check=True, env=env)
    _retention_cleanup(days=7)
    return str(target)


def restore_backup(backup_path: str) -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for restore")
    host, user, password, port, dbname = _parse_database_url(database_url)
    source = Path(backup_path)
    if not source.exists():
        raise FileNotFoundError("Backup file not found")
    env = {**os.environ, "PGPASSWORD": password} if password else os.environ.copy()
    subprocess.run(["pg_restore", "--clean", "--if-exists", "-h", host, "-p", str(port), "-U", user, "-d", dbname, str(source)], check=True, env=env)
    return database_url
