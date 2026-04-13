from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Integer, DateTime, Numeric, Boolean, event, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    id_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lock_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64), default="Submitted")
    deadline: Mapped[datetime] = mapped_column(DateTime)
    supplemental_used: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Material(Base):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    checklist_item_id: Mapped[int] = mapped_column(ForeignKey("checklist_items.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(255), default="")


class MaterialVersion(Base):
    __tablename__ = "material_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    file_path: Mapped[str] = mapped_column(String(255))
    sha256_hash: Mapped[str] = mapped_column(String(64))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    label: Mapped[str] = mapped_column(String(64), default="Pending Submission")
    correction_reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_state: Mapped[str] = mapped_column(String(64))
    to_state: Mapped[str] = mapped_column(String(64))
    allowed_role: Mapped[str] = mapped_column(String(64))


class ApplicationHistory(Base):
    __tablename__ = "application_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    from_state: Mapped[str] = mapped_column(String(64))
    to_state: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True)
    total_budget: Mapped[float] = mapped_column(Numeric(12, 2))
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    type: Mapped[str] = mapped_column(String(32))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    invoice_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class InvoiceAttachment(Base):
    __tablename__ = "invoice_attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"))
    file_path: Mapped[str] = mapped_column(String(255))
    sha256_hash: Mapped[str] = mapped_column(String(64))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class ExportRecord(Base):
    __tablename__ = "export_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    download_id: Mapped[str] = mapped_column(String(64), unique=True)
    report_type: Mapped[str] = mapped_column(String(64))
    file_path: Mapped[str] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Log(Base):
    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[str] = mapped_column(String(64))
    details: Mapped[str] = mapped_column(String(1024))
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    before_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    family_id: Mapped[str] = mapped_column(String(64))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    approval_rate: Mapped[float] = mapped_column(Numeric(8, 4))
    correction_rate: Mapped[float] = mapped_column(Numeric(8, 4))
    overspending_rate: Mapped[float] = mapped_column(Numeric(8, 4))


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(64))
    metric_value: Mapped[float] = mapped_column(Numeric(12, 6))
    threshold: Mapped[float] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("scope", "idempotency_key", name="uq_idempotency_scope_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scope: Mapped[str] = mapped_column(String(128))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_hash: Mapped[str] = mapped_column(String(64))
    response_payload: Mapped[dict] = mapped_column(JSON)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class JobLock(Base):
    __tablename__ = "job_locks"
    job_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128))
    locked_until: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class EndpointObservation(Base):
    __tablename__ = "endpoint_observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    method: Mapped[str] = mapped_column(String(16))
    path: Mapped[str] = mapped_column(String(255))
    status_code: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[int] = mapped_column(Integer)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class DataCollectionBatch(Base):
    __tablename__ = "data_collection_batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))


class QualityValidationResult(Base):
    __tablename__ = "quality_validation_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    validation_status: Mapped[str] = mapped_column(String(64))
    issues: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


def _deny_log_mutation(*args, **kwargs):
    raise ValueError("Logs are immutable and append-only")


event.listen(Log, "before_update", _deny_log_mutation)
event.listen(Log, "before_delete", _deny_log_mutation)
