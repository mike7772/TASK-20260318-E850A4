from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from app.db.session import Base, engine, SessionLocal
from app.models import config  # noqa: F401
from app.middleware.request_context import correlation_middleware
from app.middleware.idempotency import idempotency_key_middleware
from app.middleware.observability import observability_middleware
from app.services.bootstrap_service import seed_roles_and_transitions, ensure_system_admin
from app.api.v1.routers import auth, applications, files, workflow, finance, metrics, system, checklists, materials, forms
from app.jobs.metrics_job import run_daily_metrics_snapshot
from app.jobs.maintenance_job import run_maintenance
from app.jobs.gc_job import run_garbage_collection
from app.jobs.idempotency_cleanup_job import run_idempotency_cleanup
from app.jobs.backup_job import run_daily_backup
from app.services.maintenance_service import MaintenanceService
from sqlalchemy import text


def _apply_log_immutability_trigger():
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION deny_logs_mutation() RETURNS trigger AS $$
                BEGIN
                  RAISE EXCEPTION 'logs table is append-only';
                END;
                $$ LANGUAGE plpgsql;
            """))
            conn.execute(text("DROP TRIGGER IF EXISTS logs_no_update ON logs;"))
            conn.execute(text("DROP TRIGGER IF EXISTS logs_no_delete ON logs;"))
            conn.execute(text("CREATE TRIGGER logs_no_update BEFORE UPDATE ON logs FOR EACH ROW EXECUTE FUNCTION deny_logs_mutation();"))
            conn.execute(text("CREATE TRIGGER logs_no_delete BEFORE DELETE ON logs FOR EACH ROW EXECUTE FUNCTION deny_logs_mutation();"))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    boot_db = SessionLocal()
    try:
        seed_roles_and_transitions(boot_db)
        ensure_system_admin(boot_db)
    finally:
        boot_db.close()
    _apply_log_immutability_trigger()
    scan_db = SessionLocal()
    try:
        try:
            MaintenanceService(scan_db).startup_recovery_scan()
        except Exception:
            scan_db.rollback()
    finally:
        scan_db.close()
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_daily_metrics_snapshot, "cron", hour=0, minute=10, id="daily_metrics")
    scheduler.add_job(run_maintenance, "interval", minutes=15, id="maintenance_gc")
    scheduler.add_job(run_garbage_collection, "interval", minutes=20, id="storage_gc")
    scheduler.add_job(run_idempotency_cleanup, "interval", minutes=30, id="idempotency_cleanup")
    scheduler.add_job(run_daily_backup, "cron", hour=1, minute=0, id="daily_backup")
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Activity Registration and Funding Audit Platform", lifespan=lifespan)
app.middleware("http")(correlation_middleware)
app.middleware("http")(idempotency_key_middleware)
app.middleware("http")(observability_middleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")
app.include_router(finance.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(checklists.router, prefix="/api/v1")
app.include_router(materials.router, prefix="/api/v1")
app.include_router(forms.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
