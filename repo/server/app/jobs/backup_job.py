import logging
from app.services.backup_service import create_backup

logger = logging.getLogger(__name__)


def run_daily_backup():
    try:
        path = create_backup()
        logger.info("daily backup created: %s", path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("daily backup failed: %s", exc)
