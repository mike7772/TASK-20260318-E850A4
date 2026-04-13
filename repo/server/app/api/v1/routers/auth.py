import os
from fastapi import APIRouter, Depends, Request
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.api import RegisterIn, LoginIn, RefreshIn
from app.services.auth_service import AuthService
from app.api.v1.deps import get_current_user
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.core.policy_engine import permissions_for_role

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if os.getenv("ENABLE_PUBLIC_REGISTRATION", "false").lower() not in {"1", "true", "yes"}:
        # Avoid advertising registration in locked-down environments.
        raise HTTPException(status_code=404, detail="Not found")
    return AuthService(db).register(
        payload.username,
        payload.password,
        id_number=getattr(payload, "id_number", None),
        phone_number=getattr(payload, "phone_number", None),
        email=getattr(payload, "email", None),
    )


@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).login(payload.username, payload.password, request.state.correlation_id)


@router.post("/refresh")
def refresh(payload: RefreshIn, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).refresh(payload.refresh_token, request.state.correlation_id)


@router.post("/logout")
def logout(token: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    AuthService(db).logout(token)
    return {"status": "ok", "subject": decode_access_token(token)["sub"], "by": user.username}


@router.get("/me")
def me(db: Session = Depends(get_db), user=Depends(get_current_user)):
    repo = UserRepository(db)
    role = repo.get_role_by_id(user.role_id)
    return {"username": user.username, "role": role.name if role else "guest", "permissions": permissions_for_role(role.name) if role else []}
