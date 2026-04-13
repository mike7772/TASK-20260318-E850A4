import hashlib
import os
import tempfile
import time
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from fastapi import HTTPException
from fastapi import UploadFile
from app.db.uow import UnitOfWork
from app.repositories.application_repository import ApplicationRepository
from app.services.audit_service import AuditService
from app.services.idempotency_service import IdempotencyService
from app.services.validation_service import ValidationService


class FileService:
    def __init__(self, db: Session, root_dir: str = "uploads"):
        self.db = db
        self.repo = ApplicationRepository(db)
        self.audit = AuditService(db)
        self.idempotency = IdempotencyService(db)
        self.validation = ValidationService()
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    async def upload(self, *, application_id: int, checklist_item_id: int, file: UploadFile, label: str, correction_reason: str | None, actor_id: int, actor_role: str, correlation_id: str, idempotency_key: str):
        started = time.perf_counter()
        original_filename = file.filename or "upload.bin"
        content_type = file.content_type or "application/octet-stream"
        self.validation.validate_file_metadata(original_filename, content_type)
        request_payload = {
            "application_id": application_id,
            "checklist_item_id": checklist_item_id,
            "filename": original_filename,
            "label": label,
            "correction_reason": correction_reason
        }
        try:
            with UnitOfWork(self.db):
                replay, req_hash = self.idempotency.replay_or_lock(scope="file.upload", key=idempotency_key, request_payload=request_payload)
                if replay:
                    return replay
                app_obj = self.repo.get_application_for_update(application_id)
                if not app_obj:
                    raise HTTPException(status_code=404, detail="Application not found")
                if actor_role == "applicant" and app_obj.applicant_id != actor_id:
                    raise HTTPException(status_code=403, detail="Forbidden")
                used_supplemental = self.validation.validate_submission_window(app_obj.deadline, app_obj.supplemental_used, correction_reason)
                if used_supplemental:
                    app_obj.supplemental_used = True
                    app_obj.version += 1
                total_bytes = self.repo.total_upload_bytes(application_id)
                material = self.repo.find_material(application_id, checklist_item_id) or self.repo.create_material(application_id, checklist_item_id)
                versions = self.repo.get_versions(material.id)
                if len(versions) >= 3:
                    first = versions[0]
                    try:
                        os.remove(first.file_path)
                    except FileNotFoundError:
                        pass
                    self.db.delete(first)
                    for idx, version in enumerate(versions[1:], start=1):
                        version.version_number = idx
                version_number = min(len(versions) + 1, 3)
                target_dir = self.root / str(application_id) / str(checklist_item_id) / str(version_number)
                target_dir.mkdir(parents=True, exist_ok=True)
                original = original_filename
                basename = Path(original).name
                invalid = (basename != original) or (basename in {"", ".", ".."}) or (".." in original) or ("\\" in original) or ("/" in original)
                suffix = Path(basename).suffix.lower()
                if invalid or not suffix:
                    basename = f"material_upload{suffix or ''}"
                final_path = (target_dir / basename)
                try:
                    resolved_target = target_dir.resolve()
                    resolved_final = final_path.resolve()
                    if not resolved_final.is_relative_to(resolved_target):
                        raise HTTPException(status_code=400, detail="Invalid filename")
                except FileNotFoundError:
                    # If path doesn't exist yet, resolve parent and compare.
                    resolved_target = target_dir.resolve()
                    resolved_final_parent = final_path.parent.resolve()
                    if not resolved_final_parent.is_relative_to(resolved_target):
                        raise HTTPException(status_code=400, detail="Invalid filename")
                fd, temp_path = tempfile.mkstemp(dir=str(target_dir), prefix=".upload-", suffix=".tmp")
                hasher = hashlib.sha256()
                written = 0
                try:
                    with os.fdopen(fd, "wb") as tmp:
                        while True:
                            chunk = await file.read(1024 * 1024)
                            if not chunk:
                                break
                            written += len(chunk)
                            if written > self.validation.MAX_SINGLE_FILE:
                                raise HTTPException(status_code=400, detail="Single file size exceeds 20MB")
                            hasher.update(chunk)
                            tmp.write(chunk)
                        if total_bytes + written > self.validation.MAX_TOTAL_FILE:
                            raise HTTPException(status_code=400, detail="Application total file size exceeds 200MB")
                        tmp.flush()
                        os.fsync(tmp.fileno())
                    os.replace(temp_path, final_path)
                except Exception:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise
                digest = hasher.hexdigest()
                if self.repo.find_duplicate_hash(digest):
                    try:
                        os.remove(final_path)
                    except FileNotFoundError:
                        pass
                    raise HTTPException(status_code=409, detail="Duplicate material detected")
                if invalid:
                    safe_name = f"material_{digest[:16]}{suffix or ''}"
                    safe_path = target_dir / safe_name
                    os.replace(final_path, safe_path)
                    final_path = safe_path
                self.repo.add_version(
                    material_id=material.id,
                    version_number=version_number,
                    file_path=str(final_path),
                    sha256_hash=digest,
                    file_size=written,
                    label=label,
                    correction_reason=correction_reason
                )
                self.audit.log(
                    event_type="FILE_EVENT",
                    user_id=actor_id,
                    action="upload",
                    resource="material",
                    details=f"application={application_id},material={checklist_item_id},version={version_number};latency_ms={int((time.perf_counter()-started)*1000)}",
                    correlation_id=correlation_id,
                    before_snapshot={"application_id": application_id, "supplemental_used": bool(used_supplemental)},
                    after_snapshot={"sha256": digest, "file_path": str(final_path), "version": version_number}
                )
                response = {"status": "ok", "version": version_number, "sha256": digest}
                self.idempotency.store(scope="file.upload", key=idempotency_key, request_hash=req_hash, response_payload=response)
                return response
        except OperationalError as exc:
            raise HTTPException(status_code=409, detail="Concurrent upload conflict") from exc
