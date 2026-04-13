import time
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.db.uow import UnitOfWork
from app.repositories.finance_repository import FinanceRepository
from app.services.audit_service import AuditService
from app.services.idempotency_service import IdempotencyService


class FinanceService:
    _cache: dict[int, tuple[float, float]] = {}
    _ttl = 30.0

    def __init__(self, db: Session):
        self.db = db
        self.repo = FinanceRepository(db)
        self.audit = AuditService(db)
        self.idempotency = IdempotencyService(db)

    def _invalidate(self, application_id: int):
        self._cache.pop(application_id, None)

    def _expense_total_cached(self, application_id: int) -> float:
        cached = self._cache.get(application_id)
        now = time.time()
        if cached and now - cached[1] < self._ttl:
            return cached[0]
        value = self.repo.expense_total(application_id)
        self._cache[application_id] = (value, now)
        return value

    def set_budget(self, *, application_id: int, total_budget: float, actor_id: int, correlation_id: str, idempotency_key: str):
        started = time.perf_counter()
        request_payload = {"application_id": application_id, "total_budget": total_budget}
        try:
            with UnitOfWork(self.db):
                replay, req_hash = self.idempotency.replay_or_lock(scope="finance.set_budget", key=idempotency_key, request_payload=request_payload)
                if replay:
                    return replay
                budget = self.repo.get_budget_for_update(application_id)
                if budget and budget.is_locked:
                    raise HTTPException(status_code=409, detail="Budget is locked after transaction activity")
                if budget:
                    budget.total_budget = total_budget
                    budget.version += 1
                else:
                    budget = self.repo.create_budget(application_id, total_budget)
                self.audit.log(
                    event_type="FINANCE_EVENT",
                    user_id=actor_id,
                    action="set_budget",
                    resource="budget",
                    details=f"application={application_id},amount={total_budget};latency_ms={int((time.perf_counter()-started)*1000)}",
                    correlation_id=correlation_id,
                    before_snapshot={"version": budget.version - 1 if budget else None},
                    after_snapshot={"version": budget.version, "amount": total_budget}
                )
                self._invalidate(application_id)
                response = {"status": "ok", "version": budget.version}
                self.idempotency.store(scope="finance.set_budget", key=idempotency_key, request_hash=req_hash, response_payload=response)
                return response
        except OperationalError as exc:
            raise HTTPException(status_code=409, detail="Concurrent finance conflict") from exc

    def add_transaction(self, *, application_id: int, txn_type: str, amount: float, invoice_path: str | None, confirm_overspend: bool, actor_id: int, correlation_id: str, idempotency_key: str):
        started = time.perf_counter()
        request_payload = {
            "application_id": application_id,
            "txn_type": txn_type,
            "amount": amount,
            "invoice_path": invoice_path,
            "confirm_overspend": confirm_overspend
        }
        try:
            with UnitOfWork(self.db):
                replay, req_hash = self.idempotency.replay_or_lock(scope="finance.add_transaction", key=idempotency_key, request_payload=request_payload)
                if replay:
                    return replay
                budget = self.repo.get_budget_for_update(application_id)
                if not budget:
                    raise HTTPException(status_code=400, detail="Budget not set")
                current_expense = self._expense_total_cached(application_id)
                projected = current_expense + (amount if txn_type == "expense" else 0)
                if txn_type == "expense" and projected > float(budget.total_budget) * 1.1 and not confirm_overspend:
                    return {"warning": "Secondary confirmation required", "requires_confirmation": True}
                if amount <= 0:
                    raise HTTPException(status_code=400, detail="Amount must be positive")
                self.repo.add_transaction(
                    application_id=application_id,
                    type=txn_type,
                    amount=amount,
                    invoice_path=invoice_path
                )
                budget.is_locked = True
                self.audit.log(
                    event_type="FINANCE_EVENT",
                    user_id=actor_id,
                    action="add_transaction",
                    resource="transaction",
                    details=f"application={application_id},type={txn_type},amount={amount};latency_ms={int((time.perf_counter()-started)*1000)}",
                    correlation_id=correlation_id,
                    before_snapshot={"budget_locked": False},
                    after_snapshot={"budget_locked": True, "amount": amount, "type": txn_type}
                )
                self._invalidate(application_id)
                response = {"status": "recorded", "requires_confirmation": False}
                self.idempotency.store(scope="finance.add_transaction", key=idempotency_key, request_hash=req_hash, response_payload=response)
                return response
        except OperationalError as exc:
            raise HTTPException(status_code=409, detail="Concurrent finance conflict") from exc
