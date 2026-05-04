import json
import os
import subprocess
import sys
import time
from http.client import HTTPConnection
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PORT = 8765
os.environ["RAG_BACKEND"] = "local"

from backend.app.storage import clear_runtime_data


def request_json(
    method: str,
    path: str,
    body: dict | None = None,
    role: str = "clerk",
    user_id: str = "demo.clerk",
) -> tuple[int, dict]:
    connection = HTTPConnection("127.0.0.1", PORT, timeout=5)
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Content-Type": "application/json",
        "X-User-Id": user_id,
        "X-User-Role": role,
        "X-Courthouse": "Mercer",
    }
    connection.request(method, path, body=payload, headers=headers)
    response = connection.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    connection.close()
    return response.status, data


def wait_for_server() -> None:
    for _ in range(30):
        try:
            status, payload = request_json("GET", "/health")
            if status == 200 and payload["status"] == "ok":
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Local server did not start")


def main() -> None:
    clear_runtime_data()
    process = subprocess.Popen(
        [sys.executable, "-m", "backend.app.local_server"],
        cwd=ROOT,
        env={**os.environ, "PORT": str(PORT), "RAG_BACKEND": "local"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server()
        status, payload = request_json(
            "POST",
            "/api/chat",
            {"message": "What should I do next for case FM-2026-001?"},
        )
        assert status == 200
        assert payload["case"]["case_id"] == "FM-2026-001"
        assert payload["citations"]
        assert payload["citations"][0]["source_id"].startswith("SOP-FM-001")
        assert payload["approval_request"]

        status, approvals = request_json("GET", "/api/approvals")
        assert status == 200
        assert approvals["approvals"]
        action_id = approvals["approvals"][0]["action_id"]

        status, forbidden = request_json(
            "POST",
            f"/api/approvals/{action_id}/approve",
            {"reason": "clerk should not approve"},
            role="clerk",
        )
        assert status == 403
        assert "detail" in forbidden

        status, approved = request_json(
            "POST",
            f"/api/approvals/{action_id}/approve",
            {"reason": "validated case follow-up"},
            role="supervisor",
            user_id="demo.supervisor",
        )
        assert status == 200
        assert approved["approval"]["status"] == "approved"
        assert approved["approval"]["decided_by"] == "demo.supervisor"

        status, audit = request_json("GET", "/api/audit", role="admin", user_id="demo.admin")
        assert status == 200
        assert any(event["event"] == "approval_approved" for event in audit["events"])

        print("HTTP smoke test passed")
    finally:
        process.terminate()
        process.wait(timeout=5)


if __name__ == "__main__":
    main()
