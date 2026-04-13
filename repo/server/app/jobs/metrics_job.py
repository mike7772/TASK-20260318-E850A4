from app.db.session import SessionLocal
from app.services.distributed_lock_service import DistributedJobLock
from app.services.metrics_service import MetricsService


def run_daily_metrics_snapshot():
    db = SessionLocal()
    locker = DistributedJobLock(db, owner_id="metrics-job")
    try:
        if not locker.acquire("metrics_job", ttl_seconds=600):
            return
        service = MetricsService(db)
        service.backfill_missing_days(14)
        service.detect_and_correct_stale()
        service.snapshot()
    finally:
        locker.release("metrics_job")
        db.close()
