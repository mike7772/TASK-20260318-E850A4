import time
import logging
from app.db.session import SessionLocal
from app.models.models import EndpointObservation

logger = logging.getLogger(__name__)

def _operation_from_path(path: str) -> str | None:
    if "/workflow/" in path and "/transition" in path:
        return "workflow_transition"
    if "/files/upload" in path:
        return "file_upload"
    if "/finance/" in path:
        return "finance_operation"
    return None


async def observability_middleware(request, call_next):
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        try:
            db = SessionLocal()
            try:
                db.add(EndpointObservation(
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    latency_ms=elapsed_ms,
                    correlation_id=getattr(request.state, "correlation_id", None),
                    operation=_operation_from_path(request.url.path)
                ))
                db.commit()
            finally:
                db.close()
        except Exception:  # noqa: BLE001
            logger.error("observability failed")
