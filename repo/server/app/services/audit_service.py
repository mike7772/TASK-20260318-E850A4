from sqlalchemy.orm import Session
from app.models.models import Log


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        *,
        event_type: str,
        user_id: int | None,
        action: str,
        resource: str,
        details: str,
        correlation_id: str,
        actor: str | None = None,
        before_snapshot: dict | None = None,
        after_snapshot: dict | None = None
    ):
        self.db.add(Log(
            event_type=event_type,
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            correlation_id=correlation_id,
            actor=actor,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot
        ))
