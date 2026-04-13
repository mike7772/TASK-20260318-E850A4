from datetime import datetime, timedelta, timezone
from fastapi import HTTPException


class ValidationService:
    MAX_SINGLE_FILE = 20 * 1024 * 1024
    MAX_TOTAL_FILE = 200 * 1024 * 1024
    ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png"}
    ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png"}

    def validate_file_constraints(self, filename: str, content_bytes: bytes, current_total: int, content_type: str):
        suffix = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if suffix not in self.ALLOWED_EXTS:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        if content_type not in self.ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Unsupported MIME type")
        if len(content_bytes) > self.MAX_SINGLE_FILE:
            raise HTTPException(status_code=400, detail="Single file size exceeds 20MB")
        if current_total + len(content_bytes) > self.MAX_TOTAL_FILE:
            raise HTTPException(status_code=400, detail="Application total file size exceeds 200MB")

    def validate_file_metadata(self, filename: str, content_type: str):
        suffix = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if suffix not in self.ALLOWED_EXTS:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        if content_type not in self.ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Unsupported MIME type")

    def validate_submission_window(self, deadline: datetime, supplemental_used: bool, correction_reason: str | None):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if now <= deadline:
            return False
        if now > deadline + timedelta(hours=72):
            raise HTTPException(status_code=400, detail="Supplementary window expired")
        if supplemental_used:
            raise HTTPException(status_code=400, detail="Supplementary submission already used")
        if not correction_reason:
            raise HTTPException(status_code=400, detail="Correction reason required for supplementary submission")
        return True

    def validate_label_transition(self, from_label: str, to_label: str, role: str):
        allowed = {
            "Pending Submission": {"Submitted", "Needs Correction"},
            "Submitted": {"Needs Correction"},
            "Needs Correction": {"Submitted"},
        }
        if to_label not in allowed.get(from_label, set()):
            raise HTTPException(status_code=400, detail="Invalid label transition")
        if to_label == "Needs Correction" and role not in {"reviewer", "system_admin"}:
            raise HTTPException(status_code=403, detail="Forbidden")
