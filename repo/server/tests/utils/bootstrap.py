import os
from typing import Literal
from fastapi.testclient import TestClient


RoleName = Literal["applicant", "reviewer", "financial_admin", "system_admin"]


def admin_creds() -> tuple[str, str]:
    return (
        os.getenv("BOOTSTRAP_SYSTEM_ADMIN_USERNAME", "sysadmin"),
        os.getenv("BOOTSTRAP_SYSTEM_ADMIN_PASSWORD", "password"),
    )


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    body = res.json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def register_applicant(client: TestClient, username: str, password: str = "pass1234") -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"username": username, "password": password})
    return login(client, username, password)


def login_system_admin(client: TestClient) -> dict[str, str]:
    u, p = admin_creds()
    return login(client, u, p)


def provision_user(client: TestClient, admin_headers: dict[str, str], username: str, role: RoleName, password: str = "pass1234") -> dict[str, str]:
    client.post(
        "/api/v1/system/users",
        json={"username": username, "password": password, "role": role},
        headers=admin_headers,
    )
    return login(client, username, password)


def bootstrap_roles(client: TestClient) -> dict[str, dict[str, str]]:
    admin_h = login_system_admin(client)
    reviewer_h = provision_user(client, admin_h, "reviewer_test", "reviewer")
    finance_h = provision_user(client, admin_h, "finance_test", "financial_admin")
    return {"system_admin": admin_h, "reviewer": reviewer_h, "financial_admin": finance_h}

