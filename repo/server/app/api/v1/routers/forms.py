from fastapi import APIRouter, Depends, Request, HTTPException
from app.api.v1.deps import require_permission
from app.services.form_service import get_application_form_definition, validate_application_payload

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("/application")
def application_form(user=Depends(require_permission("application:create"))):
    return get_application_form_definition()


@router.post("/application/validate")
def validate_application(payload: dict, request: Request, user=Depends(require_permission("application:create"))):
    errors = validate_application_payload(payload)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    return {"status": "ok"}

