from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.deps import require_permission
from app.db.session import get_db
from app.repositories.application_repository import ApplicationRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.application_repository import ApplicationRepository as AppRepo
from app.services.validation_service import ValidationService

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("")
def list_materials(application_id: int, db: Session = Depends(get_db), user=Depends(require_permission("application:read"))):
    app = ApplicationRepository(db).get_application(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    role = getattr(user, "_role_name")
    if role == "applicant" and app.applicant_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    repo = MaterialRepository(db)
    rows = repo.list_materials_for_application(application_id)
    items = []
    for material, checklist_item in rows:
        versions = repo.list_versions_for_material(material.id)
        items.append({
            "material_id": material.id,
            "checklist_item": {"id": checklist_item.id, "code": checklist_item.code, "name": checklist_item.name},
            "versions": [
                {
                    "version": v.version_number,
                    "label": v.label,
                    "correction_reason": v.correction_reason,
                    "sha256": v.sha256_hash,
                    "size": v.file_size,
                    "uploaded_at": v.uploaded_at.isoformat(),
                }
                for v in versions
            ],
        })
    return {"application_id": application_id, "items": items}


@router.post("/{material_id}/label")
def set_label(
    material_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_permission("review:list"))
):
    label = str(payload.get("label", "")).strip()
    correction_reason = payload.get("correction_reason")
    if not label:
        raise HTTPException(status_code=400, detail="label required")
    version = AppRepo(db).latest_version_for_material(material_id)
    if not version:
        raise HTTPException(status_code=404, detail="Material not found")
    ValidationService().validate_label_transition(version.label, label, getattr(user, "_role_name"))
    version.label = label
    if correction_reason is not None:
        version.correction_reason = str(correction_reason)
    db.commit()
    return {"status": "ok", "material_id": material_id, "label": label}

