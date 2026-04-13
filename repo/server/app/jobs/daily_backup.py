from app.services.backup_service import create_backup


def run_daily_backup() -> str:
    return create_backup()
