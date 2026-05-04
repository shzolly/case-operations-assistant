import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Send } from "lucide-react";
import "./styles.css";

type Role = "clerk" | "supervisor" | "admin";

type AssistantPayload = {
  answer: string;
  citations: Array<{ source_id: string; title: string; excerpt: string }>;
  case: null | {
    case_id: string;
    case_type: string;
    status: string;
    assigned_unit: string;
    last_event: string;
    days_since_last_event: number;
    flags: string[];
  };
  approval_request: null | {
    action_id: string;
    action_type: string;
    required_role: string;
  };
  audit: {
    nodes?: string[];
  };
};

type ApprovalRecord = {
  action_id: string;
  action_type: string;
  case_id: string;
  required_role: string;
  status: "pending" | "approved" | "rejected";
  decided_by: string | null;
};

type AuditEvent = {
  event: string;
  logged_at?: string;
};

function App() {
  const [message, setMessage] = useState("What should I do next for case FM-2026-001?");
  const [role, setRole] = useState<Role>("clerk");
  const [userId, setUserId] = useState("demo.clerk");
  const [result, setResult] = useState<AssistantPayload | null>(null);
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [serviceOnline, setServiceOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [approvalBusy, setApprovalBusy] = useState(false);
  const [approvalStatus, setApprovalStatus] = useState("");
  const [approvalStatusKind, setApprovalStatusKind] = useState<"idle" | "success" | "error">("idle");

  useEffect(() => {
    setUserId(`demo.${role}`);
    setApprovalStatus(role === "clerk" ? "Clerks can create approval requests; supervisors/admins can decide them." : "");
    setApprovalStatusKind("idle");
    refreshApprovals();
    refreshAudit(role, `demo.${role}`);
  }, [role]);

  useEffect(() => {
    fetch("/health")
      .then((response) => setServiceOnline(response.ok))
      .catch(() => setServiceOnline(false));
    refreshApprovals();
  }, []);

  async function askAssistant() {
    setLoading(true);
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId,
        "X-User-Role": role,
        "X-Courthouse": "Mercer"
      },
      body: JSON.stringify({ message })
    });
    setResult(await response.json());
    await refreshApprovals();
    await refreshAudit(role, userId);
    setLoading(false);
  }

  async function refreshApprovals() {
    const response = await fetch("/api/approvals");
    const payload = await response.json();
    setApprovals(payload.approvals || []);
  }

  async function refreshAudit(currentRole = role, currentUser = userId) {
    if (currentRole !== "admin") {
      setAuditEvents([]);
      return;
    }
    const response = await fetch("/api/audit", {
      headers: {
        "X-User-Id": currentUser,
        "X-User-Role": currentRole
      }
    });
    const payload = await response.json();
    setAuditEvents((payload.events || []).slice(-6).reverse());
  }

  async function decideApproval(actionId: string, decision: "approve" | "reject") {
    setApprovalBusy(true);
    setApprovalStatus(`${decision === "approve" ? "Approving" : "Rejecting"} ${actionId}...`);
    setApprovalStatusKind("idle");
    try {
      const response = await fetch(`/api/approvals/${encodeURIComponent(actionId)}/${decision}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": userId,
          "X-User-Role": role,
          "X-Courthouse": "Mercer"
        },
        body: JSON.stringify({ reason: `${decision} from React UI` })
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || `Approval request failed with status ${response.status}`);
      }
      setApprovalStatus(`${actionId} ${payload.approval.status} by ${payload.approval.decided_by}.`);
      setApprovalStatusKind("success");
    } catch (error) {
      setApprovalStatus(`${error instanceof Error ? error.message : "Approval request failed"}. Switch to supervisor or admin role to decide approvals.`);
      setApprovalStatusKind("error");
    } finally {
      setApprovalBusy(false);
      await refreshApprovals();
      await refreshAudit(role, userId);
    }
  }

  return (
    <main className="app">
      <section className="workspace">
        <header className="masthead">
          <div>
            <p>New Jersey Judiciary</p>
            <h1>Case Operations Assistant</h1>
          </div>
          <div className={serviceOnline ? "status-pill online" : "status-pill"}>
            {serviceOnline ? "Service online" : "Service unavailable"}
          </div>
        </header>

        <section className="controls" aria-label="Demo controls">
          <label>
            Role
            <select value={role} onChange={(event) => setRole(event.target.value as Role)}>
              <option value="clerk">Clerk</option>
              <option value="supervisor">Supervisor</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <label>
            User
            <input value={userId} onChange={(event) => setUserId(event.target.value)} />
          </label>
        </section>

        <section className="quick-prompts" aria-label="Demo prompts">
          {[
            ["Family follow-up", "What should I do next for case FM-2026-001?"],
            ["Civil status", "What is the status for case SC-2026-014?"],
            ["Missing case", "What should I do next?"]
          ].map(([label, prompt]) => (
            <button className="secondary" key={label} onClick={() => setMessage(prompt)}>
              {label}
            </button>
          ))}
        </section>

        <div className="composer">
          <textarea value={message} onChange={(event) => setMessage(event.target.value)} />
          <button onClick={askAssistant} disabled={loading} aria-label="Ask assistant">
            <Send size={18} />
          </button>
        </div>

        {result && (
          <section className="answer">
            <h2>Recommendation</h2>
            <p>{result.answer}</p>
          </section>
        )}

        <section className="approvals-panel">
          <div className="section-heading">
            <h2>Approvals</h2>
            <p className={approvalStatusKind === "idle" ? "" : approvalStatusKind}>{approvalStatus}</p>
          </div>
          {approvals.length ? (
            approvals.map((approval) => (
              <article className={`item approval ${approval.status}`} key={approval.action_id}>
                <strong>{approval.action_id}</strong>
                <p>{approval.action_type} for {approval.case_id}</p>
                <p>Status: {approval.status}</p>
                {approval.status === "pending" ? (
                  <div className="approval-actions">
                    <button disabled={approvalBusy} onClick={() => decideApproval(approval.action_id, "approve")}>Approve</button>
                    <button disabled={approvalBusy} className="secondary" onClick={() => decideApproval(approval.action_id, "reject")}>
                      Reject
                    </button>
                  </div>
                ) : (
                  <p>Decided by {approval.decided_by || "unknown"}</p>
                )}
              </article>
            ))
          ) : (
            <p>No approvals recorded.</p>
          )}
        </section>
      </section>

      <aside>
        <section>
          <h2>Case Context</h2>
          {result?.case ? (
            <dl>
              <dt>Case</dt>
              <dd>{result.case.case_id}</dd>
              <dt>Type</dt>
              <dd>{result.case.case_type}</dd>
              <dt>Status</dt>
              <dd>{result.case.status}</dd>
              <dt>Unit</dt>
              <dd>{result.case.assigned_unit}</dd>
              <dt>Last Event</dt>
              <dd>{result.case.last_event}</dd>
              <dt>Flags</dt>
              <dd>{result.case.flags.join(", ") || "None"}</dd>
            </dl>
          ) : (
            <p>No case loaded.</p>
          )}
        </section>

        <section>
          <h2>Citations</h2>
          {result?.citations?.map((citation) => (
            <article className="item" key={citation.source_id}>
              <strong>{citation.source_id}</strong>
              <p>{citation.title}</p>
              <p className="excerpt">{citation.excerpt}</p>
            </article>
          ))}
        </section>

        <section>
          <h2>Workflow Trace</h2>
          <ol>
            {(result?.audit.nodes?.length ? result.audit.nodes : ["No workflow trace yet."]).map((node) => (
              <li key={node}>{node}</li>
            ))}
          </ol>
        </section>

        <section>
          <h2>Audit Events</h2>
          {role !== "admin" ? (
            <p>Switch to admin role to load audit events.</p>
          ) : auditEvents.length ? (
            auditEvents.map((event) => (
              <article className="item" key={`${event.event}-${event.logged_at}`}>
                <strong>{event.event}</strong>
                <p>{event.logged_at}</p>
              </article>
            ))
          ) : (
            <p>No audit events recorded.</p>
          )}
        </section>
      </aside>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
