from fastapi import HTTPException
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.core.fsm import FSMEngine
from app.db.uow import UnitOfWork
from app.repositories.application_repository import ApplicationRepository
from app.services.audit_service import AuditService
from app.services.idempotency_service import IdempotencyService


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ApplicationRepository(db)
        self.audit = AuditService(db)
        self.fsm = FSMEngine()
        self.idempotency = IdempotencyService(db)

    def transition(self, *, application_id: int, to_state: str, actor_role: str, actor_id: int, reason: str | None, expected_version: int, correlation_id: str, idempotency_key: str):
        started = time.perf_counter()
        request_payload = {"application_id": application_id, "to_state": to_state, "actor_role": actor_role, "reason": reason, "expected_version": expected_version}
        try:
            with UnitOfWork(self.db):
                replay, req_hash = self.idempotency.replay_or_lock(scope="workflow.transition", key=idempotency_key, request_payload=request_payload)
                if replay:
                    return replay
                app_obj = self.repo.get_application_for_update(application_id)
                if not app_obj:
                    raise HTTPException(status_code=404, detail="Application not found")
                if app_obj.version != expected_version:
                    raise HTTPException(status_code=409, detail="Version mismatch, reload application")
                from_state = app_obj.status
                result = self.fsm.validate(from_state=from_state, to_state=to_state, role=actor_role, reason=reason)
                if not result["ok"]:
                    raise HTTPException(status_code=400, detail=result["error"])
                app_obj.status = to_state
                app_obj.version += 1
                self.repo.add_history(application_id, from_state, to_state, actor_id, reason, correlation_id)
                self.audit.log(
                    event_type="WORKFLOW_EVENT",
                    user_id=actor_id,
                    action="transition",
                    resource="application",
                    details=f"{from_state}->{to_state};latency_ms={int((time.perf_counter()-started)*1000)}",
                    correlation_id=correlation_id,
                    before_snapshot={"status": from_state, "version": expected_version},
                    after_snapshot={"status": to_state, "version": app_obj.version}
                )
                response = {"status": to_state, "version": app_obj.version}
                self.idempotency.store(scope="workflow.transition", key=idempotency_key, request_hash=req_hash, response_payload=response)
                return response
        except OperationalError as exc:
            raise HTTPException(status_code=409, detail="Concurrent workflow conflict") from exc
