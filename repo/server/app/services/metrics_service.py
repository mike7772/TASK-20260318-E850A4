from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
import os
from app.models.models import Application, Budget, Transaction, MetricSnapshot, Alert


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def compute(self) -> dict:
        total = self.db.query(Application).count() or 1
        approved = self.db.query(Application).filter(Application.status == "Approved").count()
        corrected = self.db.query(Application).filter(Application.status == "Supplemented").count()
        budgets = self.db.query(Budget).all()
        overspending = 0
        for item in budgets:
            spent = self.db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                Transaction.application_id == item.application_id,
                Transaction.type == "expense"
            ).scalar()
            if float(spent) > float(item.total_budget) * 1.1:
                overspending += 1
        return {
            "approval_rate": approved / total,
            "correction_rate": corrected / total,
            "overspending_rate": overspending / (len(budgets) or 1)
        }

    def snapshot(self):
        values = self.compute()
        row = MetricSnapshot(
            snapshot_date=datetime.now(timezone.utc),
            approval_rate=values["approval_rate"],
            correction_rate=values["correction_rate"],
            overspending_rate=values["overspending_rate"]
        )
        self.db.add(row)
        self.db.commit()
        self.evaluate_alerts(values)
        return row

    def evaluate_alerts(self, values: dict):
        thresholds = {
            "approval_rate_min": float(os.getenv("ALERT_APPROVAL_RATE_MIN", "0.0")),
            "overspending_rate_max": float(os.getenv("ALERT_OVERSPENDING_RATE_MAX", "1.0")),
        }
        if values["approval_rate"] < thresholds["approval_rate_min"]:
            self.db.add(Alert(metric_name="approval_rate", metric_value=values["approval_rate"], threshold=thresholds["approval_rate_min"]))
        if values["overspending_rate"] > thresholds["overspending_rate_max"]:
            self.db.add(Alert(metric_name="overspending_rate", metric_value=values["overspending_rate"], threshold=thresholds["overspending_rate_max"]))
        self.db.commit()

    def latest(self):
        row = self.db.query(MetricSnapshot).order_by(MetricSnapshot.snapshot_date.desc()).first()
        if not row:
            return None
        return {
            "snapshot_date": row.snapshot_date.isoformat(),
            "approval_rate": float(row.approval_rate),
            "correction_rate": float(row.correction_rate),
            "overspending_rate": float(row.overspending_rate)
        }

    def backfill_missing_days(self, days: int = 7):
        now = datetime.now(timezone.utc)
        for delta in range(days):
            day = (now - timedelta(days=delta)).date()
            existing = self.db.query(MetricSnapshot).filter(
                func.date(MetricSnapshot.snapshot_date) == str(day)
            ).first()
            if not existing:
                values = self.compute()
                self.db.add(MetricSnapshot(
                    snapshot_date=datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                    approval_rate=values["approval_rate"],
                    correction_rate=values["correction_rate"],
                    overspending_rate=values["overspending_rate"]
                ))
        self.db.commit()

    def detect_and_correct_stale(self, stale_hours: int = 30):
        latest = self.db.query(MetricSnapshot).order_by(MetricSnapshot.snapshot_date.desc()).first()
        now = datetime.now(timezone.utc)
        if not latest or now - latest.snapshot_date.replace(tzinfo=timezone.utc) > timedelta(hours=stale_hours):
            self.snapshot()
