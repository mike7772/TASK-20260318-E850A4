from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.deps import require_permission
from app.db.session import get_db
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/latest")
def latest_metric(db: Session = Depends(get_db), user=Depends(require_permission("metrics:read"))):
    row = MetricsService(db).latest()
    if row:
        return row
    values = MetricsService(db).compute()
    return values
