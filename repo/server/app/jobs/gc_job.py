from app.db.session import SessionLocal
from app.services.distributed_lock_service import DistributedJobLock
from app.services.maintenance_service import MaintenanceService


def run_garbage_collection():
    db = SessionLocal()
    locker = DistributedJobLock(db, owner_id="gc-job")
    try:
        if not locker.acquire("gc_job", ttl_seconds=600):
            return
        MaintenanceService(db).gc_unused_versions()
    finally:
        locker.release("gc_job")
        db.close()
