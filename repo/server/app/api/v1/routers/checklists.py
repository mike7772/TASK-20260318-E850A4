from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.deps import require_permission
from app.repositories.checklist_repository import ChecklistRepository

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.get("/items")
def list_items(db: Session = Depends(get_db), user=Depends(require_permission("application:read"))):
    items = ChecklistRepository(db).list_items()
    return {"items": [{"id": x.id, "code": x.code, "name": x.name} for x in items]}

