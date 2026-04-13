from __future__ import annotations

import os
from sqlalchemy.orm import Session

from app.core import runtime_state
from app.core.roles import ROLES, SYSTEM_ADMIN
from app.core.security import hash_password
from app.models.models import Role, WorkflowTransition
from app.repositories.user_repository import UserRepository


DEFAULT_TRANSITIONS = [
    ("Submitted", "Supplemented", "applicant"),
    ("Submitted", "Approved", "reviewer"),
    ("Submitted", "Rejected", "reviewer"),
    ("Supplemented", "Approved", "reviewer"),
    ("Supplemented", "Rejected", "reviewer"),
    ("Submitted", "Canceled", "applicant"),
    ("Submitted", "Promoted from Waitlist", "reviewer"),
]


def seed_roles_and_transitions(db: Session):
    for name in sorted(ROLES):
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name))
    if not db.query(WorkflowTransition).first():
        for idx, rule in enumerate(DEFAULT_TRANSITIONS, 1):
            db.add(WorkflowTransition(id=idx, from_state=rule[0], to_state=rule[1], allowed_role=rule[2]))
    db.commit()


def ensure_system_admin(db: Session) -> str:
    """
    Ensures at least one system_admin exists.
    Returns the username of the ensured/admin user.
    """
    users = UserRepository(db)
    role = users.get_role(SYSTEM_ADMIN)
    if not role:
        raise RuntimeError("system_admin role missing; seed roles first")

    # If any system_admin exists, do nothing.
    from app.models.models import User  # local import to avoid cycles
    if db.query(User).filter(User.role_id == role.id).first():
        runtime_state.mark_bootstrapped()
        return db.query(User).filter(User.role_id == role.id).first().username  # type: ignore[union-attr]

    username = os.getenv("BOOTSTRAP_SYSTEM_ADMIN_USERNAME")
    password = os.getenv("BOOTSTRAP_SYSTEM_ADMIN_PASSWORD")
    if not username or not password:
        if runtime_state.get_state().is_test:
            username = "sysadmin"
            password = "password"
        else:
            raise RuntimeError("BOOTSTRAP_SYSTEM_ADMIN_USERNAME/PASSWORD must be set to create first system_admin")

    if not users.get_by_username(username):
        users.create_user(username, hash_password(password), role.id)
        db.commit()
    runtime_state.mark_bootstrapped()
    return username

