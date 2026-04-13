from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.models import MaterialVersion, Material
from app.repositories.application_repository import ApplicationRepository
from app.services.audit_service import AuditService


class MaintenanceService:
    def __init__(self, db: Session, root_dir: str = "uploads"):
        self.db = db
        self.root = Path(root_dir)
        self.repo = ApplicationRepository(db)
        self.audit = AuditService(db)

    def cleanup_orphan_files(self) -> int:
        removed = 0
        db_paths = {row.file_path for row in self.db.query(MaterialVersion).all()}
        for file in self.root.rglob("*"):
            if file.is_file() and not file.name.startswith(".upload-") and str(file) not in db_paths:
                file.unlink(missing_ok=True)
                removed += 1
        return removed

    def cleanup_expired_temp(self, older_than_minutes: int = 30) -> int:
        removed = 0
        threshold = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
        for file in self.root.rglob(".upload-*"):
            mtime = datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc)
            if mtime < threshold:
                file.unlink(missing_ok=True)
                removed += 1
        return removed

    def gc_unused_versions(self) -> int:
        removed = 0
        materials = self.db.query(Material).all()
        for material in materials:
            versions = self.repo.get_versions(material.id)
            for stale in versions[:-3]:
                Path(stale.file_path).unlink(missing_ok=True)
                self.db.delete(stale)
                removed += 1
        self.db.commit()
        return removed

    def enforce_disk_limits(self):
        apps = {m.application_id for m in self.db.query(Material).all()}
        for app_id in apps:
            if self.repo.total_upload_bytes(app_id) > 200 * 1024 * 1024:
                raise RuntimeError(f"Disk usage limit exceeded for application {app_id}")

    def startup_recovery_scan(self):
        orphan = self.cleanup_orphan_files()
        temp = self.cleanup_expired_temp()
        self.audit.log(
            event_type="FILE_EVENT",
            user_id=None,
            action="startup_recovery_scan",
            resource="storage",
            details=f"orphan_removed={orphan},temp_removed={temp}",
            correlation_id="startup-recovery",
            actor="system"
        )
        self.db.commit()
