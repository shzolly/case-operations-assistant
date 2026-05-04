import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["RAG_BACKEND"] = "local"

from backend.app.models import UserContext
from backend.app.orchestrator import answer_case_question
from backend.app.storage import clear_runtime_data, decide_approval_request, list_approval_requests, list_audit_events


def main() -> None:
    clear_runtime_data()
    user = UserContext(user_id="demo.clerk", role="clerk", courthouse="Mercer")
    response = answer_case_question("What should I do next for case FM-2026-001?", user)

    assert response.approval_request is not None
    approvals = list_approval_requests()
    assert len(approvals) == 1
    assert approvals[0]["status"] == "pending"

    updated = decide_approval_request(
        approvals[0]["action_id"],
        "rejected",
        "demo.supervisor",
        "missing supporting document",
    )
    assert updated is not None
    assert updated["status"] == "rejected"
    assert updated["decision_reason"] == "missing supporting document"

    events = list_audit_events()
    assert any(event["event"] == "approval_rejected" for event in events)
    print("Storage lifecycle test passed")


if __name__ == "__main__":
    main()
