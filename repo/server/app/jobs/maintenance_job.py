from app.db.session import SessionLocal
from app.services.distributed_lock_service import DistributedJobLock
from app.services.maintenance_service import MaintenanceService


def run_maintenance():
    db = SessionLocal()
    locker = DistributedJobLock(db, owner_id="maintenance-job")
    try:
        if not locker.acquire("maintenance_job", ttl_seconds=600):
            return
        service = MaintenanceService(db)
        service.cleanup_orphan_files()
        service.cleanup_expired_temp()
        service.enforce_disk_limits()
    finally:
        locker.release("maintenance_job")
        db.close()
