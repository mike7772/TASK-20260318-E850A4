from sqlalchemy.orm import Session
from app.models.models import ChecklistItem


class ChecklistRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str) -> ChecklistItem | None:
        return self.db.query(ChecklistItem).filter(ChecklistItem.code == code).first()

    def get_or_create(self, code: str) -> ChecklistItem:
        item = self.get_by_code(code)
        if item:
            return item
        item = ChecklistItem(code=code, name=code)
        self.db.add(item)
        self.db.flush()
        return item

    def list_items(self):
        return self.db.query(ChecklistItem).order_by(ChecklistItem.id.asc()).all()

