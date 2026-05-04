import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["RAG_BACKEND"] = "local"

from backend.app.models import UserContext
from backend.app.orchestrator import answer_case_question


def main() -> None:
    user = UserContext(user_id="demo.clerk", role="clerk", courthouse="Mercer")
    response = answer_case_question(
        "What should I do next for case FM-2026-001?",
        user,
    )

    assert response.case is not None
    assert response.case.case_id == "FM-2026-001"
    assert response.citations
    assert response.approval_request is not None
    assert "Recommended next step" in response.answer

    print("Smoke test passed")
    print(response.answer)
    assert response.citations[0].source_id.startswith("SOP-FM-001")
    print("Citations:", ", ".join(c.source_id for c in response.citations))
    print("Approval:", response.approval_request.action_type)


if __name__ == "__main__":
    main()
