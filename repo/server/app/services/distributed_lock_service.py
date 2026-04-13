from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.models import JobLock


class DistributedJobLock:
    def __init__(self, db: Session, owner_id: str | None = None):
        self.db = db
        self.owner_id = owner_id or str(uuid4())

    def acquire(self, job_name: str, ttl_seconds: int = 300) -> bool:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        until = now + timedelta(seconds=ttl_seconds)
        row = self.db.query(JobLock).filter(JobLock.job_name == job_name).with_for_update().first()
        if row and row.locked_until > now and row.owner_id != self.owner_id:
            self.db.rollback()
            return False
        if not row:
            row = JobLock(job_name=job_name, owner_id=self.owner_id, locked_until=until)
            self.db.add(row)
        else:
            row.owner_id = self.owner_id
            row.locked_until = until
            row.updated_at = now
        self.db.commit()
        return True

    def release(self, job_name: str):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        row = self.db.query(JobLock).filter(JobLock.job_name == job_name).with_for_update().first()
        if row and row.owner_id == self.owner_id:
            row.locked_until = now
            row.updated_at = now
            self.db.commit()
