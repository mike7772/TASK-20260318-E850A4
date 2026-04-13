import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    token_hash
)
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.core.policy_engine import permissions_for_role


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    def register(self, username: str, password: str, *, id_number: str | None = None, phone_number: str | None = None, email: str | None = None):
        try:
            role = self.users.get_role("applicant")
            if not role:
                raise HTTPException(status_code=400, detail="Role not found")
            if self.users.get_by_username(username):
                raise HTTPException(status_code=400, detail="User already exists")
            self.users.create_user(username, hash_password(password), role.id, id_number=id_number, phone_number=phone_number, email=email)
            self.db.commit()
            return {"message": "User created"}
        except Exception:
            self.db.rollback()
            raise

    def provision_user(self, username: str, password: str, role_name: str):
        try:
            role = self.users.get_role(role_name)
            if not role:
                raise HTTPException(status_code=400, detail="Role not found")
            if self.users.get_by_username(username):
                raise HTTPException(status_code=400, detail="User already exists")
            self.users.create_user(username, hash_password(password), role.id)
            self.db.commit()
            return {"message": "User provisioned", "username": username, "role": role_name}
        except Exception:
            self.db.rollback()
            raise

    def login(self, username: str, password: str, correlation_id: str):
        try:
            user = self.users.get_by_username(username)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if user.lock_until and now < user.lock_until:
                raise HTTPException(status_code=423, detail="Account locked for 30 minutes")
            if user.failed_window_start and now - user.failed_window_start > timedelta(minutes=5):
                user.failed_count = 0
                user.failed_window_start = now
            if not user.failed_window_start:
                user.failed_window_start = now
            if not verify_password(password, user.password_hash):
                user.failed_count += 1
                if user.failed_count >= 10 and now - user.failed_window_start <= timedelta(minutes=5):
                    user.lock_until = now + timedelta(minutes=30)
                    user.failed_count = 0
                    user.failed_window_start = None
                raise HTTPException(status_code=401, detail="Invalid credentials")
            user.failed_count = 0
            user.failed_window_start = None
            user.lock_until = None
            role = self.users.get_role_by_id(user.role_id)
            family_id = secrets.token_hex(16)
            access = create_access_token(user.username, role.name, permissions_for_role(role.name))
            refresh = create_refresh_token(user.username, family_id)
            refresh_payload = decode_access_token(refresh)
            self.users.save_refresh(user.id, token_hash(refresh), family_id, datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc))
            self.audit.log(event_type="AUTH_EVENT", user_id=user.id, action="login", resource="auth", details="login success", correlation_id=correlation_id)
            self.db.commit()
            return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
        except Exception:
            self.db.rollback()
            raise

    def refresh(self, refresh_token: str, correlation_id: str):
        try:
            payload = decode_access_token(refresh_token)
            if payload.get("typ") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            record = self.users.get_refresh(token_hash(refresh_token))
            if not record:
                raise HTTPException(status_code=401, detail="Refresh token not found")
            if record.is_revoked:
                self.users.revoke_family(record.family_id)
                raise HTTPException(status_code=401, detail="Token reuse detected")
            record.is_revoked = True
            user = self.users.get_by_username(payload["sub"])
            role = self.users.get_role_by_id(user.role_id)
            access = create_access_token(user.username, role.name, permissions_for_role(role.name))
            new_refresh = create_refresh_token(user.username, record.family_id)
            refresh_payload = decode_access_token(new_refresh)
            self.users.save_refresh(user.id, token_hash(new_refresh), record.family_id, datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc))
            self.audit.log(event_type="AUTH_EVENT", user_id=user.id, action="refresh", resource="auth", details="token rotated", correlation_id=correlation_id)
            self.db.commit()
            return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}
        except Exception:
            self.db.rollback()
            raise

    def logout(self, access_token: str):
        payload = decode_access_token(access_token)
        self.users.revoke_jti(payload["jti"])
        self.db.commit()
