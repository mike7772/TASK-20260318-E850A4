from __future__ import annotations

import os
from app.db.session import Base, engine, SessionLocal
from app.services.bootstrap_service import seed_roles_and_transitions, ensure_system_admin


def setup_session():
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("JWT_SECRET", "test-secret")
    os.environ.setdefault("ENCRYPTION_KEY", "test-key")
    os.environ.setdefault("ENABLE_PUBLIC_REGISTRATION", "true")
    os.environ.setdefault("BOOTSTRAP_SYSTEM_ADMIN_USERNAME", "sysadmin")
    os.environ.setdefault("BOOTSTRAP_SYSTEM_ADMIN_PASSWORD", "password")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_roles_and_transitions(db)
        ensure_system_admin(db)
    finally:
        db.close()


def teardown_session():
    Base.metadata.drop_all(bind=engine)


def reset_between_tests():
    # Strong isolation: rebuild schema each test to avoid ordering dependence.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_roles_and_transitions(db)
        ensure_system_admin(db)
    finally:
        db.close()

