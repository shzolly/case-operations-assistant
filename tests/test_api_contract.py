from fastapi.testclient import TestClient

from backend.app.api import app
from backend.app.storage import clear_runtime_data


def test_chat_creates_cited_approval_request() -> None:
    clear_runtime_data()
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={"message": "What should I do next for case FM-2026-001?"},
        headers={"X-User-Role": "clerk", "X-User-Id": "demo.clerk"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case"]["case_id"] == "FM-2026-001"
    assert payload["citations"]
    assert payload["citations"][0]["source_id"].startswith("SOP-FM-001")
    assert payload["approval_request"]["required_role"] == "supervisor"
    assert payload["audit"]["nodes"] == [
        "extract_case_id",
        "authorize_read",
        "load_case",
        "retrieve_policy",
        "decide_action",
        "compose_response",
        "finalize",
    ]


def test_clerk_cannot_approve_sensitive_action() -> None:
    clear_runtime_data()
    client = TestClient(app)
    chat = client.post(
        "/api/chat",
        json={"message": "What should I do next for case FM-2026-001?"},
        headers={"X-User-Role": "clerk", "X-User-Id": "demo.clerk"},
    )
    action_id = chat.json()["approval_request"]["action_id"]

    response = client.post(
        f"/api/approvals/{action_id}/approve",
        json={"reason": "not allowed"},
        headers={"X-User-Role": "clerk", "X-User-Id": "demo.clerk"},
    )

    assert response.status_code == 403


def test_supervisor_approves_and_admin_reads_audit() -> None:
    clear_runtime_data()
    client = TestClient(app)
    chat = client.post(
        "/api/chat",
        json={"message": "What should I do next for case FM-2026-001?"},
        headers={"X-User-Role": "clerk", "X-User-Id": "demo.clerk"},
    )
    action_id = chat.json()["approval_request"]["action_id"]

    approval = client.post(
        f"/api/approvals/{action_id}/approve",
        json={"reason": "validated follow-up"},
        headers={"X-User-Role": "supervisor", "X-User-Id": "demo.supervisor"},
    )
    assert approval.status_code == 200
    assert approval.json()["approval"]["status"] == "approved"

    audit = client.get(
        "/api/audit",
        headers={"X-User-Role": "admin", "X-User-Id": "demo.admin"},
    )
    assert audit.status_code == 200
    assert any(event["event"] == "approval_approved" for event in audit.json()["events"])
