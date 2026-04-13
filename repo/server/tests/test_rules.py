import hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine
from tests.utils.bootstrap import register_applicant, login_system_admin, provision_user

client = TestClient(app)


def create_app(headers):
    resp = client.post("/api/v1/applications", json={"title": "A1", "deadline": (datetime.utcnow() + timedelta(days=1)).isoformat()}, headers=headers)
    return resp.json()["id"], resp.json()["version"]


def setup_module():
    with TestClient(app):
        pass


def test_rbac_enforced():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "app1")
    reviewer_h = provision_user(client, admin_h, "rev1", "reviewer")
    app_id, version = create_app(applicant_h)
    bad = client.post(f"/api/v1/workflow/{app_id}/transition", json={"to_state": "Approved", "expected_version": version}, headers={**applicant_h, "Idempotency-Key": "rbac-1"})
    assert bad.status_code == 403
    ok = client.post(f"/api/v1/workflow/{app_id}/transition", json={"to_state": "Approved", "expected_version": version}, headers={**reviewer_h, "Idempotency-Key": "rbac-2"})
    assert ok.status_code == 200


def test_fsm_invalid_transition():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "app2")
    reviewer_h = provision_user(client, admin_h, "rev2", "reviewer")
    app_id, version = create_app(applicant_h)
    bad = client.post(f"/api/v1/workflow/{app_id}/transition", json={"to_state": "Canceled", "expected_version": version}, headers={**reviewer_h, "Idempotency-Key": "fsm-1"})
    assert bad.status_code in (400, 403)


def test_concurrency_version_mismatch():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "app3")
    reviewer_h = provision_user(client, admin_h, "rev3", "reviewer")
    app_id, version = create_app(applicant_h)
    first = client.post(f"/api/v1/workflow/{app_id}/transition", json={"to_state": "Approved", "expected_version": version}, headers={**reviewer_h, "Idempotency-Key": "ver-1"})
    assert first.status_code == 200
    second = client.post(f"/api/v1/workflow/{app_id}/transition", json={"to_state": "Rejected", "expected_version": version, "reason": "late"}, headers={**reviewer_h, "Idempotency-Key": "ver-2"})
    assert second.status_code == 409


def test_file_hash_collision_and_limit():
    applicant_h = register_applicant(client, "app4")
    app_id, _ = create_app(applicant_h)
    first = client.post(
        "/api/v1/files/upload",
        data={"application_id": str(app_id), "material_type": "1"},
        files={"file": ("a.pdf", b"same", "application/pdf")},
        headers={**applicant_h, "Idempotency-Key": "file-1"},
    )
    assert first.status_code == 200
    second = client.post(
        "/api/v1/files/upload",
        data={"application_id": str(app_id), "material_type": "1"},
        files={"file": ("b.pdf", b"same", "application/pdf")},
        headers={**applicant_h, "Idempotency-Key": "file-2"},
    )
    assert second.status_code == 409


def test_deadline_and_supplement_window():
    applicant_h = register_applicant(client, "app5")
    past = datetime.utcnow() - timedelta(hours=1)
    app_id = client.post("/api/v1/applications", json={"title": "Past", "deadline": past.isoformat()}, headers=applicant_h).json()["id"]
    ok = client.post(
        "/api/v1/files/upload",
        data={"application_id": str(app_id), "material_type": "1", "label": "Needs Correction", "correction_reason": "fix"},
        files={"file": ("ok.pdf", b"x", "application/pdf")},
        headers={**applicant_h, "Idempotency-Key": "sup-1"},
    )
    assert ok.status_code == 200
    denied = client.post(
        "/api/v1/files/upload",
        data={"application_id": str(app_id), "material_type": "1", "label": "Needs Correction", "correction_reason": "again"},
        files={"file": ("again.pdf", b"y", "application/pdf")},
        headers={**applicant_h, "Idempotency-Key": "sup-2"},
    )
    assert denied.status_code == 400


def test_finance_overspend_and_budget_lock():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "app6")
    finance_h = provision_user(client, admin_h, "fin6", "financial_admin")
    app_id, _ = create_app(applicant_h)
    set_b = client.post("/api/v1/finance/budget", json={"application_id": app_id, "total_budget": 100}, headers={**finance_h, "Idempotency-Key": "fin-1"})
    assert set_b.status_code == 200
    warn = client.post("/api/v1/finance/transactions", json={"application_id": app_id, "type": "expense", "amount": 120, "confirm_overspend": False}, headers={**finance_h, "Idempotency-Key": "fin-2"})
    assert warn.json()["requires_confirmation"] is True
    accept = client.post("/api/v1/finance/transactions", json={"application_id": app_id, "type": "expense", "amount": 120, "confirm_overspend": True}, headers={**finance_h, "Idempotency-Key": "fin-3"})
    assert accept.status_code == 200
    lock = client.post("/api/v1/finance/budget", json={"application_id": app_id, "total_budget": 200}, headers={**finance_h, "Idempotency-Key": "fin-4"})
    assert lock.status_code == 409


def test_idempotency_replay():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "app7")
    app_id, version = create_app(applicant_h)
    reviewer_h = provision_user(client, admin_h, "rev7", "reviewer")
    headers = {**reviewer_h, "Idempotency-Key": "idem-1"}
    one = client.post(f"/api/v1/workflow/{app_id}/transition", json={"to_state": "Approved", "expected_version": version}, headers=headers)
    two = client.post(f"/api/v1/workflow/{app_id}/transition", json={"to_state": "Approved", "expected_version": version}, headers=headers)
    assert one.status_code == 200 and two.status_code == 200
    assert one.json() == two.json()


def test_concurrent_workflow_race():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "app8")
    reviewer_h = provision_user(client, admin_h, "rev8", "reviewer")
    app_id, version = create_app(applicant_h)

    def worker(i: int):
        return client.post(
            f"/api/v1/workflow/{app_id}/transition",
            json={"to_state": "Approved", "expected_version": version},
            headers={**reviewer_h, "Idempotency-Key": f"race-{i}"}
        ).status_code

    with ThreadPoolExecutor(max_workers=20) as pool:
        codes = list(pool.map(worker, range(20)))
    assert codes.count(200) == 1
    assert any(code == 409 for code in codes)


def test_concurrent_file_upload_same_material():
    applicant_h = register_applicant(client, "app9")
    app_id, _ = create_app(applicant_h)

    def worker(i: int):
        return client.post(
            "/api/v1/files/upload",
            data={"application_id": str(app_id), "material_type": "99"},
            files={"file": (f"f{i}.pdf", b"blob", "application/pdf")},
            headers={**applicant_h, "Idempotency-Key": f"u-{i}"}
        ).status_code

    with ThreadPoolExecutor(max_workers=10) as pool:
        codes = list(pool.map(worker, range(10)))
    assert any(code == 200 for code in codes)


def test_concurrent_finance_updates():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "app10")
    finance_h = provision_user(client, admin_h, "fin10", "financial_admin")
    app_id, _ = create_app(applicant_h)
    client.post("/api/v1/finance/budget", json={"application_id": app_id, "total_budget": 300}, headers={**finance_h, "Idempotency-Key": "base-budget"})

    def worker(i: int):
        return client.post(
            "/api/v1/finance/transactions",
            json={"application_id": app_id, "type": "expense", "amount": 10, "confirm_overspend": True},
            headers={**finance_h, "Idempotency-Key": f"t-{i}"}
        ).status_code

    with ThreadPoolExecutor(max_workers=15) as pool:
        codes = list(pool.map(worker, range(15)))
    assert all(code in (200, 409) for code in codes)


def test_binary_upload_sha256_mime_and_size():
    applicant_h = register_applicant(client, "app_binary")
    app_id, _ = create_app(applicant_h)
    blob = b"\x89PNG\r\n\x1a\n\x00\x01binary"
    ok = client.post(
        "/api/v1/files/upload",
        data={"application_id": str(app_id), "material_type": "1"},
        files={"file": ("img.png", blob, "image/png")},
        headers={**applicant_h, "Idempotency-Key": "bin-ok"},
    )
    assert ok.status_code == 200
    assert ok.json()["sha256"] == hashlib.sha256(blob).hexdigest()
    bad_mime = client.post(
        "/api/v1/files/upload",
        data={"application_id": str(app_id), "material_type": "2"},
        files={"file": ("evil.pdf", b"abc", "text/plain")},
        headers={**applicant_h, "Idempotency-Key": "bin-mime"},
    )
    assert bad_mime.status_code == 400
    too_big = client.post(
        "/api/v1/files/upload",
        data={"application_id": str(app_id), "material_type": "3"},
        files={"file": ("huge.pdf", b"a" * (20 * 1024 * 1024 + 1), "application/pdf")},
        headers={**applicant_h, "Idempotency-Key": "bin-size"},
    )
    assert too_big.status_code == 400


def test_object_level_application_and_finance_filtering():
    admin_h = login_system_admin(client)
    user_a = register_applicant(client, "owner_a")
    user_b = register_applicant(client, "owner_b")
    fin = provision_user(client, admin_h, "owner_fin", "financial_admin")
    a_id, _ = create_app(user_a)
    b_id, _ = create_app(user_b)
    client.post("/api/v1/finance/budget", json={"application_id": a_id, "total_budget": 100}, headers={**fin, "Idempotency-Key": "obj-budget-a"})
    client.post("/api/v1/finance/budget", json={"application_id": b_id, "total_budget": 100}, headers={**fin, "Idempotency-Key": "obj-budget-b"})
    client.post("/api/v1/finance/transactions", json={"application_id": a_id, "type": "expense", "amount": 10, "confirm_overspend": True}, headers={**fin, "Idempotency-Key": "obj-fin-a"})
    client.post("/api/v1/finance/transactions", json={"application_id": b_id, "type": "expense", "amount": 10, "confirm_overspend": True}, headers={**fin, "Idempotency-Key": "obj-fin-b"})
    apps_for_a = client.get("/api/v1/applications", headers=user_a)
    app_ids = {x["id"] for x in apps_for_a.json()["items"]}
    assert a_id in app_ids and b_id not in app_ids
    tx_for_a = client.get("/api/v1/finance/transactions", headers=user_a)
    tx_ids = {x["application_id"] for x in tx_for_a.json()["items"]}
    assert a_id in tx_ids and b_id not in tx_ids


def test_batch_review_limits_and_partial_success():
    admin_h = login_system_admin(client)
    applicant = register_applicant(client, "batch_app")
    reviewer = provision_user(client, admin_h, "batch_rev", "reviewer")
    app_id, version = create_app(applicant)
    too_many = [{"application_id": app_id, "to_state": "Approved", "expected_version": version} for _ in range(51)]
    rejected = client.post("/api/v1/workflow/batch-review", json=too_many, headers={**reviewer, "Idempotency-Key": "batch-too-many"})
    assert rejected.status_code == 400
    mixed = [
        {"application_id": app_id, "to_state": "Approved", "expected_version": version},
        {"application_id": app_id, "to_state": "Rejected", "expected_version": 999, "reason": "x"},
    ]
    partial = client.post("/api/v1/workflow/batch-review", json=mixed, headers={**reviewer, "Idempotency-Key": "batch-partial"})
    assert partial.status_code in (200, 207)
    assert len(partial.json()["results"]) == 2
    assert any(r["status"] == "ok" for r in partial.json()["results"])
    assert any(r["status"] == "failed" for r in partial.json()["results"])


def test_upload_forbidden_for_other_users_application():
    user_a = register_applicant(client, "up_a")
    user_b = register_applicant(client, "up_b")
    app_id, _ = create_app(user_a)
    forbidden = client.post(
        "/api/v1/files/upload",
        data={"application_id": str(app_id), "material_type": "1"},
        files={"file": ("x.pdf", b"x", "application/pdf")},
        headers={**user_b, "Idempotency-Key": "up-forbidden"},
    )
    assert forbidden.status_code == 403


def test_workflow_history_endpoint():
    admin_h = login_system_admin(client)
    applicant_h = register_applicant(client, "hist_app")
    reviewer_h = provision_user(client, admin_h, "hist_rev", "reviewer")
    app_id, version = create_app(applicant_h)
    tr = client.post(
        f"/api/v1/workflow/{app_id}/transition",
        json={"to_state": "Approved", "expected_version": version},
        headers={**reviewer_h, "Idempotency-Key": "hist-transition"},
    )
    assert tr.status_code == 200
    history = client.get(f"/api/v1/workflow/{app_id}/history", headers=reviewer_h)
    assert history.status_code == 200
    assert len(history.json()["items"]) >= 1
    row = history.json()["items"][0]
    assert "from_state" in row and "to_state" in row and "actor" in row and "timestamp" in row and "correlation_id" in row
