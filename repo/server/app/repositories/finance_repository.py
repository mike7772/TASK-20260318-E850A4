from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.models import Budget, Transaction, Application


class FinanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_budget_for_update(self, application_id: int) -> Budget | None:
        return self.db.query(Budget).filter(Budget.application_id == application_id).with_for_update().first()

    def create_budget(self, application_id: int, total_budget: float) -> Budget:
        budget = Budget(application_id=application_id, total_budget=total_budget)
        self.db.add(budget)
        self.db.flush()
        return budget

    def has_transactions(self, application_id: int) -> bool:
        return self.db.query(Transaction).filter(Transaction.application_id == application_id).first() is not None

    def add_transaction(self, **kwargs):
        transaction = Transaction(**kwargs)
        self.db.add(transaction)
        return transaction

    def expense_total(self, application_id: int) -> float:
        value = self.db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.application_id == application_id,
            Transaction.type == "expense"
        ).scalar()
        return float(value or 0)

    def list_transactions(self, application_id: int | None, txn_type: str | None, sort_by: str, sort_dir: str, page: int, size: int, current_user_id: int, current_role: str):
        query = self.db.query(Transaction).join(Application, Application.id == Transaction.application_id)
        if current_role == "applicant":
            query = query.filter(Application.applicant_id == current_user_id)
        if application_id:
            query = query.filter(Transaction.application_id == application_id)
        if txn_type:
            query = query.filter(Transaction.type == txn_type)
        sort_col = getattr(Transaction, sort_by, Transaction.id)
        if sort_dir == "desc":
            sort_col = sort_col.desc()
        total = query.count()
        items = query.order_by(sort_col).offset((page - 1) * size).limit(size).all()
        return total, items
