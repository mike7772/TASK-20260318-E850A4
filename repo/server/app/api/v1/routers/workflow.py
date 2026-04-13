from fastapi import APIRouter, Depends, Request, HTTPException
import logging
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.api.v1.deps import require_permission
from app.db.session import get_db
from app.repositories.application_repository import ApplicationRepository
from app.schemas.api import TransitionIn
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["workflow"])
logger = logging.getLogger(__name__)


@router.post("/{application_id}/transition")
def transition_state(application_id: int, payload: TransitionIn, request: Request, db: Session = Depends(get_db), user=Depends(require_permission("workflow:transition"))):
    return WorkflowService(db).transition(
        application_id=application_id,
        to_state=payload.to_state,
        actor_role=getattr(user, "_role_name"),
        actor_id=user.id,
        reason=payload.reason,
        expected_version=payload.expected_version,
        correlation_id=request.state.correlation_id,
        idempotency_key=request.state.idempotency_key
    )


@router.get("/reviews")
def list_reviews(
    status: str | None = None,
    sort_by: str = "id",
    sort_dir: str = "asc",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(require_permission("review:list"))
):
    total, rows = ApplicationRepository(db).list_applications(
        status, sort_by, sort_dir, page, min(size, 100), user.id, getattr(user, "_role_name")
    )
    return {"total": total, "items": [{"id": r.id, "status": r.status, "version": r.version} for r in rows], "reviewer": user.username}


@router.post("/batch-review")
def batch_review(payload: list[dict], request: Request, db: Session = Depends(get_db), user=Depends(require_permission("workflow:transition"))):
    if len(payload) > 50:
        raise HTTPException(status_code=400, detail="Batch limit is 50")
    service = WorkflowService(db)
    results: list[dict] = []
    for item in payload:
        try:
            result = service.transition(
                application_id=item["application_id"],
                to_state=item["to_state"],
                actor_role=getattr(user, "_role_name"),
                actor_id=user.id,
                reason=item.get("reason"),
                expected_version=item["expected_version"],
                correlation_id=request.state.correlation_id,
                idempotency_key=f"{request.state.idempotency_key}-{item['application_id']}"
            )
            results.append({"item_id": item["application_id"], "status": "ok", "result": result})
        except HTTPException as exc:
            if exc.status_code == 403:
                code = "AUTH_DENIED"
                msg = "Forbidden"
            elif exc.status_code == 409:
                code = "VERSION_CONFLICT"
                msg = "Version conflict"
            elif exc.status_code == 400:
                code = "VALIDATION_ERROR"
                msg = "Validation error"
            else:
                code = "INTERNAL_ERROR"
                msg = "Internal error"
            results.append({"item_id": item.get("application_id"), "status": "failed", "error_code": code, "message": msg})
        except Exception as exc:  # noqa: BLE001
            logger.exception("batch review item failed: %s", item.get("application_id"))
            results.append({"item_id": item.get("application_id"), "status": "failed", "error_code": "INTERNAL_ERROR", "message": "Internal error"})
    ok_count = sum(1 for r in results if r.get("status") == "ok")
    if ok_count == 0:
        return JSONResponse(status_code=400, content={"count": len(payload), "results": results})
    if ok_count != len(results):
        return JSONResponse(status_code=207, content={"count": len(payload), "results": results})
    return {"count": len(payload), "results": results}


@router.get("/{application_id}/history")
def get_application_history(
    application_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission("review:list"))
):
    app = ApplicationRepository(db).get_application(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    role = getattr(user, "_role_name")
    if role == "applicant" and app.applicant_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    rows = ApplicationRepository(db).list_history(application_id)
    return {
        "application_id": application_id,
        "items": [
            {
                "from_state": r.from_state,
                "to_state": r.to_state,
                "actor": r.changed_by,
                "timestamp": r.changed_at.isoformat(),
                "reason": r.reason,
                "correlation_id": r.correlation_id,
            }
            for r in rows
        ],
    }
