from sqlalchemy.orm import Session


class UnitOfWork:
    def __init__(self, db: Session):
        self.db = db
        self._tx = None

    def __enter__(self):
        self._tx = self.db.begin_nested() if self.db.in_transaction() else self.db.begin()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self._tx.rollback()
        else:
            self._tx.commit()
        return False
