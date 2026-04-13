from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class EncryptedConfig(Base):
    __tablename__ = "encrypted_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(128), unique=True)
    value_encrypted: Mapped[str] = mapped_column(String(4096))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

