from backend.app.models import UserContext
from backend.app.storage import clear_runtime_data
from backend.app.workflow import CASE_WORKFLOW_GRAPH, run_case_workflow


def test_langgraph_compiled_workflow_is_available() -> None:
    assert CASE_WORKFLOW_GRAPH is not None
    assert hasattr(CASE_WORKFLOW_GRAPH, "invoke")


def test_langgraph_executes_main_case_path() -> None:
    clear_runtime_data()
    user = UserContext(user_id="demo.clerk", role="clerk", courthouse="Mercer")

    response = run_case_workflow("What should I do next for case FM-2026-001?", user)

    assert response.audit["nodes"] == [
        "extract_case_id",
        "authorize_read",
        "load_case",
        "retrieve_policy",
        "decide_action",
        "compose_response",
        "finalize",
    ]

