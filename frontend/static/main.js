const message = document.querySelector("#message");
const role = document.querySelector("#role");
const userId = document.querySelector("#userId");
const askButton = document.querySelector("#askButton");
const answerText = document.querySelector("#answerText");
const caseContext = document.querySelector("#caseContext");
const citations = document.querySelector("#citations");
const approvals = document.querySelector("#approvals");
const auditEvents = document.querySelector("#auditEvents");
const workflowTrace = document.querySelector("#workflowTrace");
const serviceStatus = document.querySelector("#serviceStatus");
const quickPrompts = document.querySelector(".quick-prompts");
const approvalStatus = document.querySelector("#approvalStatus");
let approvalBusy = false;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderCase(caseRecord) {
  if (!caseRecord) {
    caseContext.innerHTML = "<dt>Status</dt><dd>No case loaded.</dd>";
    return;
  }

  caseContext.innerHTML = `
    <dt>Case</dt><dd>${escapeHtml(caseRecord.case_id)}</dd>
    <dt>Status</dt><dd>${escapeHtml(caseRecord.status)}</dd>
    <dt>Unit</dt><dd>${escapeHtml(caseRecord.assigned_unit)}</dd>
    <dt>Last Event</dt><dd>${escapeHtml(caseRecord.last_event)}</dd>
    <dt>Idle Days</dt><dd>${escapeHtml(caseRecord.days_since_last_event)}</dd>
    <dt>Flags</dt><dd>${escapeHtml((caseRecord.flags || []).join(", ") || "None")}</dd>
  `;
}

function renderCitations(items) {
  if (!items.length) {
    citations.textContent = "No citations returned.";
    return;
  }

  citations.innerHTML = items
    .map(
      (item) => `
        <article class="item">
          <strong>${escapeHtml(item.source_id)}</strong>
          <p>${escapeHtml(item.title)}</p>
          <p class="excerpt">${escapeHtml(item.excerpt)}</p>
        </article>
      `
    )
    .join("");
}

function renderWorkflow(audit) {
  const nodes = audit?.nodes || [];
  if (!nodes.length) {
    workflowTrace.innerHTML = "<li>No workflow trace yet.</li>";
    return;
  }
  workflowTrace.innerHTML = nodes.map((node) => `<li>${escapeHtml(node)}</li>`).join("");
}

async function refreshApprovals() {
  const response = await fetch("/api/approvals");
  const payload = await response.json();
  if (!payload.approvals.length) {
    approvals.textContent = "No approvals recorded.";
    return;
  }

  approvals.innerHTML = payload.approvals
    .map(
      (item) => `
        <article class="item approval ${escapeHtml(item.status)}">
          <strong>${escapeHtml(item.action_id)}</strong>
          <p>${escapeHtml(item.action_type)} for ${escapeHtml(item.case_id)}</p>
          <p>Status: ${escapeHtml(item.status)}</p>
          ${
            item.status === "pending"
              ? `<div class="approval-actions">
                  <button data-decision="approve" data-action-id="${escapeHtml(item.action_id)}" ${approvalBusy ? "disabled" : ""}>Approve</button>
                  <button class="secondary" data-decision="reject" data-action-id="${escapeHtml(item.action_id)}" ${approvalBusy ? "disabled" : ""}>Reject</button>
                </div>`
              : `<p>Decided by ${escapeHtml(item.decided_by || "unknown")}</p>`
          }
        </article>
      `
    )
    .join("");
}

async function refreshAudit() {
  if (role.value !== "admin") {
    auditEvents.textContent = "Switch to admin role to load audit events.";
    return;
  }
  const response = await fetch("/api/audit", {
    headers: {
      "X-User-Id": userId.value,
      "X-User-Role": role.value
    }
  });
  const payload = await response.json();
  const events = (payload.events || []).slice(-6).reverse();
  if (!events.length) {
    auditEvents.textContent = "No audit events recorded.";
    return;
  }
  auditEvents.innerHTML = events
    .map(
      (event) => `
        <article class="item">
          <strong>${escapeHtml(event.event)}</strong>
          <p>${escapeHtml(event.logged_at || "")}</p>
        </article>
      `
    )
    .join("");
}

async function decideApproval(actionId, decision) {
  const endpoint = decision === "approve" ? "approve" : "reject";
  approvalBusy = true;
  approvalStatus.textContent = `${decision === "approve" ? "Approving" : "Rejecting"} ${actionId}...`;
  approvalStatus.className = "";
  await refreshApprovals();

  try {
    const response = await fetch(`/api/approvals/${encodeURIComponent(actionId)}/${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId.value || "demo.supervisor",
        "X-User-Role": role.value,
        "X-Courthouse": "Mercer"
      },
      body: JSON.stringify({ reason: `${decision} from local MVP UI` })
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || `Approval request failed with status ${response.status}`);
    }
    approvalStatus.textContent = `${actionId} ${payload.approval.status} by ${payload.approval.decided_by}.`;
    approvalStatus.className = "success";
  } catch (error) {
    approvalStatus.textContent = `${error.message}. Switch to supervisor or admin role to decide approvals.`;
    approvalStatus.className = "error";
  } finally {
    approvalBusy = false;
    await refreshApprovals();
    await refreshAudit();
  }
}

async function askAssistant() {
  askButton.disabled = true;
  askButton.textContent = "Asking";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId.value,
        "X-User-Role": role.value,
        "X-Courthouse": "Mercer"
      },
      body: JSON.stringify({ message: message.value })
    });

    const payload = await response.json();
    answerText.textContent = payload.answer;
    renderCase(payload.case);
    renderCitations(payload.citations || []);
    renderWorkflow(payload.audit);
    await refreshApprovals();
    await refreshAudit();
  } finally {
    askButton.disabled = false;
    askButton.textContent = "Ask";
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    serviceStatus.textContent = response.ok ? "Service online" : "Service unavailable";
    serviceStatus.classList.toggle("online", response.ok);
  } catch {
    serviceStatus.textContent = "Service offline";
  }
}

askButton.addEventListener("click", askAssistant);
role.addEventListener("change", async () => {
  userId.value = `demo.${role.value}`;
  approvalStatus.textContent = role.value === "clerk" ? "Clerks can create approval requests; supervisors/admins can decide them." : "";
  approvalStatus.className = "";
  await refreshApprovals();
  await refreshAudit();
});
quickPrompts.addEventListener("click", (event) => {
  const target = event.target;
  if (target instanceof HTMLButtonElement && target.dataset.prompt) {
    message.value = target.dataset.prompt;
  }
});
approvals.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) {
    return;
  }
  const actionId = target.dataset.actionId;
  const decision = target.dataset.decision;
  if (actionId && decision) {
    await decideApproval(actionId, decision);
  }
});
workflowTrace.innerHTML = "<li>No workflow trace yet.</li>";
checkHealth();
refreshApprovals();
refreshAudit();
