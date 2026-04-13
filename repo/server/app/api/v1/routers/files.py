from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.api.v1.deps import require_permission
from app.db.session import get_db
from app.repositories.checklist_repository import ChecklistRepository
from app.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    request: Request,
    application_id: int = Form(...),
    material_type: str = Form(...),
    label: str = Form("Submitted"),
    correction_reason: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_permission("file:upload"))
):
    if material_type.isdigit():
        checklist_item_id = int(material_type)
    else:
        checklist_item_id = ChecklistRepository(db).get_or_create(material_type).id
    return await FileService(db).upload(
        application_id=application_id,
        checklist_item_id=checklist_item_id,
        file=file,
        label=label,
        correction_reason=correction_reason,
        actor_id=user.id,
        actor_role=getattr(user, "_role_name"),
        correlation_id=request.state.correlation_id,
        idempotency_key=request.state.idempotency_key
    )
