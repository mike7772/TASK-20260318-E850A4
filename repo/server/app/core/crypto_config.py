import os
from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY must be provided")
    return Fernet(key.encode("utf-8"))


def encrypt_config_value(raw_value: str) -> str:
    return _get_fernet().encrypt(raw_value.encode("utf-8")).decode("utf-8")


def decrypt_config_value(encrypted_value: str) -> str:
    return _get_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
