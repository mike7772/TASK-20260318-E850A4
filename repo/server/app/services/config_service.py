from sqlalchemy.orm import Session
from app.core.crypto_config import encrypt_config_value, decrypt_config_value
from app.models.config import EncryptedConfig


class ConfigService:
    def __init__(self, db: Session):
        self.db = db

    def set_secret(self, key: str, value: str):
        row = self.db.query(EncryptedConfig).filter(EncryptedConfig.key == key).first()
        if not row:
            row = EncryptedConfig(key=key, value_encrypted=encrypt_config_value(value))
            self.db.add(row)
        else:
            row.value_encrypted = encrypt_config_value(value)
        self.db.commit()
        return {"status": "ok", "key": key}

    def get_secret(self, key: str):
        row = self.db.query(EncryptedConfig).filter(EncryptedConfig.key == key).first()
        if not row:
            return None
        return {"key": key, "value": decrypt_config_value(row.value_encrypted)}

