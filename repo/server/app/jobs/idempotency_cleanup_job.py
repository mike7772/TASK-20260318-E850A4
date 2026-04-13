from app.db.session import SessionLocal
from app.services.distributed_lock_service import DistributedJobLock
from app.services.idempotency_service import IdempotencyService


def run_idempotency_cleanup():
    db = SessionLocal()
    locker = DistributedJobLock(db, owner_id="idempotency-cleanup-job")
    try:
        if not locker.acquire("idempotency_cleanup_job", ttl_seconds=600):
            return
        IdempotencyService(db).cleanup_expired()
    finally:
        locker.release("idempotency_cleanup_job")
        db.close()
