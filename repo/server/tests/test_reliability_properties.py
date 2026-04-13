import random
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.fsm import FSMEngine, TRANSITIONS
from app.db.session import Base, engine
from tests.utils.bootstrap import register_applicant, login_system_admin, provision_user

client = TestClient(app)


def setup_module():
    # Schema lifecycle is handled centrally via tests/conftest.py
    return


def _bootstrap():
    admin_h = login_system_admin(client)
    reviewer_h = provision_user(client, admin_h, "prop_r", "reviewer")
    finance_h = provision_user(client, admin_h, "prop_f", "financial_admin")
    applicant_h = register_applicant(client, "prop_a")
    return applicant_h, reviewer_h, finance_h


def create_app(headers):
    res = client.post("/api/v1/applications", json={"title": "prop", "deadline": (datetime.utcnow() + timedelta(days=1)).isoformat()}, headers=headers)
    body = res.json()
    return body["id"], body["version"]


def test_fsm_property_randomized_transitions():
    engine = FSMEngine()
    applicant_h, reviewer_h, _finance_h = _bootstrap()
    headers_by_role = {"applicant": applicant_h, "reviewer": reviewer_h}
    allowed = {(t.from_state, t.to_state, t.role) for t in TRANSITIONS}

    for idx in range(50):
        app_id, version = create_app(applicant_h)
        state = "Submitted"
        for step in range(random.randint(1, 5)):
            role = random.choice(["applicant", "reviewer"])
            to_state = random.choice(["Supplemented", "Approved", "Rejected", "Canceled", "Promoted from Waitlist"])
            reason = "r" if to_state == "Rejected" else None
            expected_engine_ok = (state, to_state, role) in allowed and (to_state != "Rejected" or reason is not None)
            val = engine.validate(from_state=state, to_state=to_state, role=role, reason=reason)
            assert val["ok"] == expected_engine_ok
            expected_api_ok = role == "reviewer" and expected_engine_ok
            resp = client.post(
                f"/api/v1/workflow/{app_id}/transition",
                json={"to_state": to_state, "expected_version": version, "reason": reason},
                headers={**headers_by_role[role], "Idempotency-Key": f"prop-{idx}-{step}-{role}"}
            )
            if expected_api_ok:
                assert resp.status_code == 200
                version = resp.json()["version"]
                state = to_state
            else:
                assert resp.status_code in (400, 403, 409)


def test_long_run_soak_stability():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "soak_a")
    reviewer_h = provision_user(client, admin_h, "soak_r", "reviewer")
    finance_h = provision_user(client, admin_h, "soak_f", "financial_admin")
    app_id, version = create_app(applicant_h)
    client.post("/api/v1/finance/budget", json={"application_id": app_id, "total_budget": 10000}, headers={**finance_h, "Idempotency-Key": "soak-budget"})

    for i in range(60):
        client.post(
            "/api/v1/files/upload",
            data={"application_id": str(app_id), "material_type": str(i % 3)},
            files={"file": (f"s{i}.pdf", f"blob-{i}".encode("utf-8"), "application/pdf")},
            headers={**applicant_h, "Idempotency-Key": f"soak-upload-{i}"}
        )
        client.post(
            "/api/v1/finance/transactions",
            json={"application_id": app_id, "type": "expense", "amount": 10, "confirm_overspend": True},
            headers={**finance_h, "Idempotency-Key": f"soak-fin-{i}"}
        )
        if i == 0:
            tr = client.post(
                f"/api/v1/workflow/{app_id}/transition",
                json={"to_state": "Approved", "expected_version": version},
                headers={**reviewer_h, "Idempotency-Key": "soak-transition"}
            )
            if tr.status_code == 200:
                version = tr.json()["version"]

    metrics = client.get("/api/v1/metrics/latest", headers=finance_h)
    assert metrics.status_code == 200
