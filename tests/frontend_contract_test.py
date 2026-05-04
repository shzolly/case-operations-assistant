from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_INDEX = ROOT / "frontend" / "static" / "index.html"
STATIC_MAIN = ROOT / "frontend" / "static" / "main.js"
REACT_MAIN = ROOT / "frontend" / "src" / "main.tsx"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> None:
    html = read(STATIC_INDEX)
    static_js = read(STATIC_MAIN)
    react = read(REACT_MAIN)

    required_static_ids = [
        "serviceStatus",
        "workflowTrace",
        "caseContext",
        "citations",
        "approvals",
        "auditEvents",
    ]
    for element_id in required_static_ids:
        assert f'id="{element_id}"' in html

    assert html.index('class="answer"') < html.index('class="approvals-panel"')
    assert html.index('id="workflowTrace"') > html.index("<aside>")

    required_static_behaviors = [
        "/api/chat",
        "/api/approvals",
        "/api/audit",
        "data-decision=\"approve\"",
        "renderWorkflow",
        "refreshAudit",
        "approvalStatus",
    ]
    for behavior in required_static_behaviors:
        assert behavior in static_js

    required_react_behaviors = [
        "Workflow Trace",
        "Audit Events",
        "quick-prompts",
        "decideApproval",
        "refreshAudit",
        "Service online",
    ]
    for behavior in required_react_behaviors:
        assert behavior in react

    print("Frontend contract test passed")


if __name__ == "__main__":
    main()
