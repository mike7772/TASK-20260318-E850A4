from app.core.roles import APPLICANT, REVIEWER, FINANCIAL_ADMIN, SYSTEM_ADMIN, is_valid_role

POLICIES = {
    APPLICANT: {"application:create", "file:upload", "application:read"},
    REVIEWER: {"workflow:transition", "review:list", "application:read"},
    FINANCIAL_ADMIN: {"finance:budget", "finance:transaction", "metrics:read", "application:read"},
    SYSTEM_ADMIN: {"*"},
}


def authorize(role: str, permission: str) -> bool:
    if not is_valid_role(role):
        return False
    perms = POLICIES.get(role, set())
    return "*" in perms or permission in perms


def permissions_for_role(role: str) -> list[str]:
    return sorted(POLICIES.get(role, set()))
