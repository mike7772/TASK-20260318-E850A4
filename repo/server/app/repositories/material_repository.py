from sqlalchemy.orm import Session
from app.models.models import Material, MaterialVersion, ChecklistItem


class MaterialRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_materials_for_application(self, application_id: int):
        return (
            self.db.query(Material, ChecklistItem)
            .join(ChecklistItem, ChecklistItem.id == Material.checklist_item_id)
            .filter(Material.application_id == application_id)
            .order_by(Material.id.asc())
            .all()
        )

    def list_versions_for_material(self, material_id: int):
        return (
            self.db.query(MaterialVersion)
            .filter(MaterialVersion.material_id == material_id)
            .order_by(MaterialVersion.version_number.asc())
            .all()
        )

