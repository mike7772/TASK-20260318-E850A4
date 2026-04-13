from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.api.v1.deps import require_permission
from app.db.session import get_db
from app.repositories.application_repository import ApplicationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.api import CreateApplicationIn
from app.services.audit_service import AuditService
from app.utils.privacy import mask_id_number, mask_phone, mask_phone_partial, mask_email, mask_email_partial

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("")
def create_application(payload: CreateApplicationIn, request: Request, db: Session = Depends(get_db), user=Depends(require_permission("application:create"))):
    app_obj = ApplicationRepository(db).create_application(user.id, payload.title, payload.deadline)
    AuditService(db).log(
        event_type="WORKFLOW_EVENT",
        user_id=user.id,
        action="create_application",
        resource="application",
        details=payload.title,
        correlation_id=request.state.correlation_id
    )
    db.commit()
    return {"id": app_obj.id, "status": app_obj.status, "version": app_obj.version}


@router.get("")
def list_applications(
    status: str | None = None,
    sort_by: str = "id",
    sort_dir: str = "asc",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(require_permission("application:read"))
):
    total, items = ApplicationRepository(db).list_applications(
        status, sort_by, sort_dir, page, min(size, 100), user.id, getattr(user, "_role_name")
    )
    role = getattr(user, "_role_name")
    users = UserRepository(db)
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            (lambda owner: {
                "id": x.id,
                "title": x.title,
                "status": x.status,
                "version": x.version,
                "owner_masked": mask_id_number(owner.id_number) if owner and owner.id_number else None,
                "owner_contact": {
                    "id_number": (owner.id_number if role == "system_admin" else mask_id_number(owner.id_number)) if owner and owner.id_number else None,
                    "phone_number": (
                        owner.phone_number if role == "system_admin" else (mask_phone_partial(owner.phone_number) if role == "reviewer" else mask_phone(owner.phone_number))
                    ) if owner and owner.phone_number else None,
                    "email": (
                        owner.email if role == "system_admin" else (mask_email_partial(owner.email) if role == "reviewer" else mask_email(owner.email))
                    ) if owner and owner.email else None,
                },
            })(users.get_by_id(x.applicant_id))
            for x in items
        ],
        "viewer": user.username
    }
