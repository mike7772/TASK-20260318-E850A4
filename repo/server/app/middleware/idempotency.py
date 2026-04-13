from fastapi import Request
from fastapi.responses import JSONResponse


CRITICAL_PREFIXES = (
    "/api/v1/files/upload",
    "/api/v1/workflow/",
    "/api/v1/finance/transactions",
    "/api/v1/finance/budget",
)


async def idempotency_key_middleware(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH"} and request.url.path.startswith(CRITICAL_PREFIXES):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return JSONResponse(status_code=400, content={"detail": "Idempotency-Key header required"})
        request.state.idempotency_key = key
    return await call_next(request)
