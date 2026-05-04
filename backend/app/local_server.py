import json
import os
from dataclasses import asdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend.app.models import UserContext
from backend.app.orchestrator import answer_case_question
from backend.app.security import APPROVE_SENSITIVE_ACTION, REVIEW_AUDIT, has_permission
from backend.app.storage import decide_approval_request, list_approval_requests, list_audit_events


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend" / "static"
RUNTIME_DIR = ROOT / ".runtime"
REQUEST_LOG = RUNTIME_DIR / "local-server-requests.log"


def log_request_path(method: str, path: str) -> None:
    RUNTIME_DIR.mkdir(exist_ok=True)
    with REQUEST_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{method} {path}\n")


class LocalMvpHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-User-Id, X-User-Role, X-Courthouse")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        log_request_path("GET", path)
        if path == "/health":
            self._send_json({"status": "ok"})
            return
        if path == "/api/approvals":
            self._send_json({"approvals": list_approval_requests()})
            return
        if path == "/api/audit":
            role = self.headers.get("X-User-Role", "admin")
            if not has_permission(role, REVIEW_AUDIT):
                self._send_json({"detail": "Role cannot review audit trail"}, HTTPStatus.FORBIDDEN)
                return
            self._send_json({"events": list_audit_events()})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        log_request_path("POST", path)
        if path.startswith("/api/approvals/") and path.endswith("/approve"):
            self._handle_approval_decision(path, "approved")
            return
        if path.startswith("/api/approvals/") and path.endswith("/reject"):
            self._handle_approval_decision(path, "rejected")
            return
        if path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return

        body = self._read_json_body()
        user = UserContext(
            user_id=self.headers.get("X-User-Id", "demo.clerk"),
            role=self.headers.get("X-User-Role", "clerk"),
            courthouse=self.headers.get("X-Courthouse", "Mercer"),
        )
        response = answer_case_question(str(body.get("message", "")), user)
        self._send_json(asdict(response))

    def _handle_approval_decision(self, path: str, decision: str) -> None:
        role = self.headers.get("X-User-Role", "supervisor")
        user_id = self.headers.get("X-User-Id", "demo.supervisor")
        if not has_permission(role, APPROVE_SENSITIVE_ACTION):
            self._send_json({"detail": "Role cannot decide sensitive actions"}, HTTPStatus.FORBIDDEN)
            return

        body = self._read_json_body()
        parts = path.strip("/").split("/")
        action_id = parts[2]
        updated = decide_approval_request(
            action_id,
            decision,
            user_id,
            body.get("reason"),
        )
        if updated is None:
            self._send_json({"detail": "Approval request not found"}, HTTPStatus.NOT_FOUND)
            return
        self._send_json({"approval": updated})

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), LocalMvpHandler)
    print(f"NJ Judiciary MVP server running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
