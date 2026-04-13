from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.models import Application, Material, MaterialVersion, WorkflowTransition, ApplicationHistory


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_application(self, applicant_id: int, title: str, deadline):
        app_obj = Application(applicant_id=applicant_id, title=title, deadline=deadline, status="Submitted")
        self.db.add(app_obj)
        self.db.flush()
        return app_obj

    def get_application_for_update(self, application_id: int) -> Application | None:
        return self.db.query(Application).filter(Application.id == application_id).with_for_update().first()

    def get_application(self, application_id: int) -> Application | None:
        return self.db.query(Application).filter(Application.id == application_id).first()

    def list_applications(self, status: str | None, sort_by: str, sort_dir: str, page: int, size: int, current_user_id: int, current_role: str):
        query = self.db.query(Application)
        if current_role == "applicant":
            query = query.filter(Application.applicant_id == current_user_id)
        if status:
            query = query.filter(Application.status == status)
        sort_col = getattr(Application, sort_by, Application.id)
        if sort_dir == "desc":
            sort_col = sort_col.desc()
        total = query.count()
        items = query.order_by(sort_col).offset((page - 1) * size).limit(size).all()
        return total, items

    def find_material(self, application_id: int, checklist_item_id: int) -> Material | None:
        return self.db.query(Material).filter(
            Material.application_id == application_id,
            Material.checklist_item_id == checklist_item_id
        ).with_for_update().first()

    def create_material(self, application_id: int, checklist_item_id: int):
        material = Material(application_id=application_id, checklist_item_id=checklist_item_id)
        self.db.add(material)
        self.db.flush()
        return material

    def find_duplicate_hash(self, sha256_hash: str) -> bool:
        return self.db.query(MaterialVersion).filter(MaterialVersion.sha256_hash == sha256_hash).first() is not None

    def get_versions(self, material_id: int):
        return self.db.query(MaterialVersion).filter(MaterialVersion.material_id == material_id).order_by(MaterialVersion.version_number.asc()).all()

    def latest_version_for_material(self, material_id: int) -> MaterialVersion | None:
        return self.db.query(MaterialVersion).filter(MaterialVersion.material_id == material_id).order_by(MaterialVersion.version_number.desc()).first()

    def add_version(self, **kwargs):
        version = MaterialVersion(**kwargs)
        self.db.add(version)
        return version

    def total_upload_bytes(self, application_id: int) -> int:
        total = self.db.query(func.coalesce(func.sum(MaterialVersion.file_size), 0)).join(
            Material, MaterialVersion.material_id == Material.id
        ).filter(Material.application_id == application_id).scalar()
        return int(total or 0)

    def get_transition(self, from_state: str, to_state: str, role: str) -> WorkflowTransition | None:
        return self.db.query(WorkflowTransition).filter(
            WorkflowTransition.from_state == from_state,
            WorkflowTransition.to_state == to_state,
            WorkflowTransition.allowed_role == role
        ).first()

    def add_history(self, application_id: int, from_state: str, to_state: str, changed_by: int, reason: str | None, correlation_id: str):
        self.db.add(ApplicationHistory(
            application_id=application_id,
            from_state=from_state,
            to_state=to_state,
            changed_by=changed_by,
            reason=reason,
            correlation_id=correlation_id
        ))

    def list_history(self, application_id: int):
        return self.db.query(ApplicationHistory).filter(
            ApplicationHistory.application_id == application_id
        ).order_by(ApplicationHistory.changed_at.desc()).all()
