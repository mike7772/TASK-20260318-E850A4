from __future__ import annotations

ROLES = {
    "applicant",
    "reviewer",
    "financial_admin",
    "system_admin",
}

APPLICANT = "applicant"
REVIEWER = "reviewer"
FINANCIAL_ADMIN = "financial_admin"
SYSTEM_ADMIN = "system_admin"


def is_valid_role(role: str) -> bool:
    return role in ROLES

