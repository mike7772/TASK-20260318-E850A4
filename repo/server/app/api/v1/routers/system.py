from datetime import datetime
import csv
from pathlib import Path
import secrets
import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.api.v1.deps import require_permission
from app.schemas.api import RestoreIn, ProvisionUserIn
from app.services.backup_service import create_backup, restore_backup
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.models import Application, ExportRecord, Budget, Transaction, User, Role
from app.core.policy_engine import permissions_for_role
from app.services.auth_service import AuthService
from app.services.config_service import ConfigService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/duplicate-check")
def duplicate_check(user=Depends(require_permission("system:admin"))):
    return {"enabled": False, "note": "Reserved endpoint for local similarity/duplicate checks"}


@router.get("/export")
def export_report(
    report_type: Literal["audit", "finance", "compliance", "whitelist"],
    db: Session = Depends(get_db),
    user=Depends(require_permission("system:admin"))
):
    target_dir = Path(os.getenv("EXPORT_DIR", "/exports"))
    target_dir.mkdir(parents=True, exist_ok=True)
    download_id = secrets.token_hex(16)
    file_path = target_dir / f"{download_id}.csv"
    with file_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if report_type == "audit":
            rows = db.query(Application.id, Application.status, Application.version).order_by(Application.id.asc()).all()
            writer.writerow(["application_id", "status", "version"])
            for row in rows:
                writer.writerow([row.id, row.status, row.version])
        elif report_type == "finance":
            rows = db.query(Application.id, Budget.total_budget).join(Budget, Budget.application_id == Application.id).order_by(Application.id.asc()).all()
            writer.writerow(["application_id", "total_budget"])
            for row in rows:
                writer.writerow([row.id, float(row.total_budget)])
        elif report_type == "compliance":
            rows = db.query(Application.id, Application.status, Application.supplemental_used).order_by(Application.id.asc()).all()
            writer.writerow(["application_id", "status", "supplemental_used"])
            for row in rows:
                writer.writerow([row.id, row.status, bool(row.supplemental_used)])
        elif report_type == "whitelist":
            rows = (
                db.query(User.username, Role.name)
                .join(Role, Role.id == User.role_id)
                .order_by(User.username.asc())
                .all()
            )
            writer.writerow(["username", "role", "permissions"])
            for row in rows:
                writer.writerow([row.username, row.name, " ".join(permissions_for_role(row.name))])
        else:
            raise HTTPException(status_code=400, detail="Unsupported report type")
    db.add(ExportRecord(download_id=download_id, report_type=report_type, file_path=str(file_path), created_by=user.id))
    db.commit()
    return {"download_id": download_id}


@router.get("/export/{download_id}")
def download_export(download_id: str, db: Session = Depends(get_db), user=Depends(require_permission("system:admin"))):
    record = db.query(ExportRecord).filter(ExportRecord.download_id == download_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    path = Path(record.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(str(path), media_type="text/csv", filename=f"{record.report_type}.csv")


@router.post("/users")
def provision_user(payload: ProvisionUserIn, db: Session = Depends(get_db), user=Depends(require_permission("system:admin"))):
    return AuthService(db).provision_user(payload.username, payload.password, payload.role)


@router.post("/config/secret")
def set_secret(payload: dict, db: Session = Depends(get_db), user=Depends(require_permission("system:admin"))):
    key = str(payload.get("key", "")).strip()
    value = str(payload.get("value", "")).strip()
    if not key or not value:
        raise HTTPException(status_code=400, detail="key and value required")
    return ConfigService(db).set_secret(key, value)


@router.get("/config/secret/{key}")
def get_secret(key: str, db: Session = Depends(get_db), user=Depends(require_permission("system:admin"))):
    row = ConfigService(db).get_secret(key)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return row


@router.post("/recovery/backup")
def backup_now(user=Depends(require_permission("system:admin"))):
    return {"backup_path": create_backup(), "by": user.username}


@router.post("/recovery/restore")
def restore_now(payload: RestoreIn, user=Depends(require_permission("system:admin"))):
    return {"restored_db": restore_backup(payload.backup_path), "by": user.username}
