from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.core.policy_engine import authorize
from app.db.session import get_db
from app.models.models import User
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    repo = UserRepository(db)
    if payload.get("jti") and repo.is_jti_revoked(payload["jti"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    user = repo.get_by_username(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_permission(permission: str):
    def checker(request: Request, current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        repo = UserRepository(db)
        role = repo.get_role_by_id(current.role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        allowed = authorize(role.name, permission)
        AuditService(db).log(
            event_type="AUTH_EVENT",
            user_id=current.id,
            action="authorize",
            resource=permission,
            details="ALLOW" if allowed else "DENY",
            correlation_id=getattr(request.state, "correlation_id", "n/a"),
            actor=current.username
        )
        if not allowed:
            db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        db.commit()
        current._role_name = role.name  # noqa: SLF001
        return current
    return checker
