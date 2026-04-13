import hashlib
import os
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.deps import require_permission
from app.db.session import get_db
from app.repositories.finance_repository import FinanceRepository
from app.schemas.api import BudgetIn, TxnIn
from app.services.finance_service import FinanceService
from app.models.models import InvoiceAttachment, Transaction, Application
from app.services.validation_service import ValidationService

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("/budget")
def set_budget(payload: BudgetIn, request: Request, db: Session = Depends(get_db), user=Depends(require_permission("finance:budget"))):
    return FinanceService(db).set_budget(
        application_id=payload.application_id,
        total_budget=payload.total_budget,
        actor_id=user.id,
        correlation_id=request.state.correlation_id,
        idempotency_key=request.state.idempotency_key
    )


@router.post("/transactions")
def add_transaction(payload: TxnIn, request: Request, db: Session = Depends(get_db), user=Depends(require_permission("finance:transaction"))):
    return FinanceService(db).add_transaction(
        application_id=payload.application_id,
        txn_type=payload.type,
        amount=payload.amount,
        invoice_path=payload.invoice_path,
        confirm_overspend=payload.confirm_overspend,
        actor_id=user.id,
        correlation_id=request.state.correlation_id,
        idempotency_key=request.state.idempotency_key
    )


@router.get("/transactions")
def list_transactions(
    application_id: int | None = None,
    txn_type: str | None = None,
    sort_by: str = "id",
    sort_dir: str = "asc",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(require_permission("finance:transaction"))
):
    total, items = FinanceRepository(db).list_transactions(
        application_id, txn_type, sort_by, sort_dir, page, min(size, 100), user.id, getattr(user, "_role_name")
    )
    return {"total": total, "page": page, "size": size, "items": [{"id": x.id, "application_id": x.application_id, "type": x.type, "amount": float(x.amount)} for x in items], "viewer": user.username}


@router.post("/transactions/{transaction_id}/invoice")
async def upload_invoice(
    transaction_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_permission("finance:transaction"))
):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    app = db.query(Application).filter(Application.id == txn.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    role = getattr(user, "_role_name")
    if role == "applicant" and app.applicant_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    original_filename = file.filename or "invoice.bin"
    content_type = file.content_type or "application/octet-stream"
    ValidationService().validate_file_metadata(original_filename, content_type)
    target_dir = Path("uploads") / "invoices" / str(transaction_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    original = original_filename
    basename = Path(original).name
    invalid = (basename != original) or (basename in {"", ".", ".."}) or (".." in original) or ("\\" in original) or ("/" in original)
    suffix = Path(basename).suffix.lower()
    if invalid:
        basename = f"invoice_upload{suffix or ''}"
    fd, temp_path = tempfile.mkstemp(dir=str(target_dir), prefix=".inv-", suffix=".tmp")
    final_path = target_dir / basename
    try:
        resolved_target = target_dir.resolve()
        resolved_final = final_path.resolve()
        if not resolved_final.is_relative_to(resolved_target):
            raise HTTPException(status_code=400, detail="Invalid filename")
    except FileNotFoundError:
        resolved_target = target_dir.resolve()
        resolved_final_parent = final_path.parent.resolve()
        if not resolved_final_parent.is_relative_to(resolved_target):
            raise HTTPException(status_code=400, detail="Invalid filename")
    hasher = hashlib.sha256()
    written = 0
    try:
        with os.fdopen(fd, "wb") as tmp:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > ValidationService.MAX_SINGLE_FILE:
                    raise HTTPException(status_code=400, detail="Single file size exceeds 20MB")
                hasher.update(chunk)
                tmp.write(chunk)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(temp_path, final_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    digest = hasher.hexdigest()
    if invalid:
        safe_name = f"invoice_{digest[:16]}{suffix or ''}"
        safe_path = target_dir / safe_name
        os.replace(final_path, safe_path)
        final_path = safe_path
    txn.invoice_path = str(final_path)
    db.add(InvoiceAttachment(transaction_id=transaction_id, file_path=str(final_path), sha256_hash=digest, file_size=written))
    db.commit()
    return {"status": "ok", "transaction_id": transaction_id, "sha256": digest}
