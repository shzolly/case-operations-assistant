import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.models import ApprovalRequest


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
APPROVALS_FILE = DATA_DIR / "pending_approvals.json"
AUDIT_FILE = DATA_DIR / "audit-log.jsonl"


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def list_approval_requests() -> list[dict[str, Any]]:
    ensure_data_dir()
    if not APPROVALS_FILE.exists():
        return []
    approvals = json.loads(APPROVALS_FILE.read_text(encoding="utf-8"))
    return [_normalize_approval(item) for item in approvals]


def _normalize_approval(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "pending",
        "decided_by": None,
        "decided_at": None,
        "decision_reason": None,
        **item,
    }


def save_approval_request(request: ApprovalRequest) -> None:
    approvals = list_approval_requests()
    if any(item["action_id"] == request.action_id for item in approvals):
        return
    approvals.append(
        {
            **asdict(request),
            "status": "pending",
            "decided_by": None,
            "decided_at": None,
            "decision_reason": None,
        }
    )
    APPROVALS_FILE.write_text(
        json.dumps(approvals, indent=2, default=_json_default),
        encoding="utf-8",
    )


def decide_approval_request(
    action_id: str,
    decision: str,
    decided_by: str,
    reason: str | None = None,
) -> dict[str, Any] | None:
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be approved or rejected")

    approvals = list_approval_requests()
    updated = None
    for item in approvals:
        if item["action_id"] == action_id:
            item["status"] = decision
            item["decided_by"] = decided_by
            item["decided_at"] = datetime.now(timezone.utc).isoformat()
            item["decision_reason"] = reason
            updated = item
            break

    if updated is None:
        return None

    APPROVALS_FILE.write_text(
        json.dumps(approvals, indent=2, default=_json_default),
        encoding="utf-8",
    )
    append_audit_event(
        {
            "event": f"approval_{decision}",
            "action_id": action_id,
            "decided_by": decided_by,
            "reason": reason,
        }
    )
    return updated


def append_audit_event(event: dict[str, Any]) -> None:
    ensure_data_dir()
    event = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=_json_default) + "\n")


def list_audit_events(limit: int = 100) -> list[dict[str, Any]]:
    ensure_data_dir()
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines if line.strip()]
    return events[-limit:]


def clear_runtime_data() -> None:
    ensure_data_dir()
    for path in (APPROVALS_FILE, AUDIT_FILE):
        if path.exists():
            path.unlink()
