import hashlib
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import IdempotencyRecord


class IdempotencyService:
    def __init__(self, db: Session):
        self.db = db
        self.ttl_hours = 24

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def replay_or_lock(self, *, scope: str, key: str, request_payload: dict):
        req_hash = self._hash(json.dumps(request_payload, sort_keys=True, separators=(",", ":")))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        existing = self.db.query(IdempotencyRecord).filter(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.idempotency_key == key,
            IdempotencyRecord.expires_at > now
        ).with_for_update().first()
        if not existing:
            return None, req_hash
        if existing.request_hash != req_hash:
            raise HTTPException(status_code=409, detail="Idempotency key reused with different payload")
        return existing.response_payload, req_hash

    def store(self, *, scope: str, key: str, request_hash: str, response_payload: dict, status_code: int = 200):
        payload = json.dumps(response_payload, sort_keys=True, separators=(",", ":"))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.add(IdempotencyRecord(
            scope=scope,
            idempotency_key=key,
            request_hash=request_hash,
            response_hash=self._hash(payload),
            response_payload=response_payload,
            status_code=status_code,
            expires_at=now + timedelta(hours=self.ttl_hours)
        ))

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        deleted = self.db.query(IdempotencyRecord).filter(IdempotencyRecord.expires_at <= now).delete(synchronize_session=False)
        self.db.commit()
        return deleted
