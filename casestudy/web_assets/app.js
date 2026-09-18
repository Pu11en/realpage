(() => {
  "use strict";

  const state = { payload: null, active: 0 };
  const byId = (id) => document.getElementById(id);
  const encoder = new TextEncoder();

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[char]);
  }

  function oneBytes(index = state.active) {
    if (!state.payload) return "";
    return state.payload.records[index].submission_line + "\n";
  }

  function allBytes() {
    return state.payload ? state.payload.submission_jsonl : "";
  }

  function showToast(message) {
    const toast = byId("toast");
    toast.textContent = message;
    toast.hidden = false;
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => { toast.hidden = true; }, 1800);
  }

  async function copyText(text, label) {
    await navigator.clipboard.writeText(text);
    showToast(label);
  }

  function downloadText(text) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([text], { type: "application/x-ndjson;charset=utf-8" }));
    link.download = "case-study-submission.jsonl";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(link.href), 0);
  }

  function statusMark(status) {
    if (status === "passed" || status === "measured") return { icon: "✓", cls: "passed" };
    if (status === "failed") return { icon: "×", cls: "failed" };
    return { icon: "?", cls: status || "unsupported" };
  }

  function words(value) {
    return String(value || "").replaceAll("_", " ").replace(/\s+/g, " ").trim();
  }

  function sentence(value) {
    const text = words(value);
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : "Not provided";
  }

  function channelLabel(channel) {
    return ({ sms: "Text message", email: "Email", voice: "Human phone call" })[channel] || sentence(channel);
  }

  function formatSendAt(value) {
    const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2})?(Z|[+-]\d{2}:\d{2})$/);
    if (!match) return value || "Not scheduled";
    const [, year, month, day, rawHour, minute, rawOffset] = match;
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const hour = Number(rawHour);
    const displayHour = hour % 12 || 12;
    const period = hour >= 12 ? "PM" : "AM";
    const offset = rawOffset === "Z" ? "UTC" : `UTC${rawOffset.replace("-", "−")}`;
    return `${months[Number(month) - 1]} ${Number(day)}, ${year} at ${displayHour}:${minute} ${period} (${offset})`;
  }

  function actionLabel(action) {
    if (!action) return "No next step supplied";
    if (action.type === "start_cadence") return `Start ${words(action.name)}`;
    if (action.type === "follow_up_in_days") return `Follow up in ${action.value} ${action.value === 1 ? "day" : "days"}`;
    if (action.type === "mark_opted_out") return "Mark this person opted out";
    if (action.type === "suppress") return "Do not contact this person";
    if (action.type === "escalate") return "Send this record to a human";
    if (action.type === "create_call_task") return "Create a human call task";
    return sentence(action.type);
  }

  function decisionSummary(answer) {
    if (answer.next_message) {
      const label = answer.next_message.channel === "sms" ? "Send text" : `Send ${answer.next_message.channel}`;
      return { label, cls: "send" };
    }
    if (answer.next_action?.type === "create_call_task") return { label: "Human call", cls: "call" };
    if (answer.next_action?.type === "escalate") return { label: "Human review", cls: "review" };
    return { label: "Do not send", cls: "hold" };
  }

  function ctaLabel(cta) {
    if (!cta) return "";
    if (Array.isArray(cta.options) && cta.options.length) return `Reply choices: ${cta.options.join(" or ")}`;
    if (cta.link) return `Tour link: ${cta.link}`;
    if (cta.type === "schedule_tour") return "Ask them to reply to arrange a tour";
    return sentence(cta.type);
  }

  function noMessageTitle(action) {
    if (action?.type === "mark_opted_out") return "Do not send. Mark this person opted out.";
    if (action?.type === "create_call_task") return "Do not send a text or email. Create a call task.";
    if (action?.type === "escalate") return "Do not send. A human needs to review this.";
    return "No message should be sent.";
  }

  function renderHumanAnswer(answer, diagnostics) {
    const message = answer.next_message;
    const action = answer.next_action;
    const decision = decisionSummary(answer);
    const badge = byId("human-decision-badge");
    badge.textContent = decision.label;
    badge.className = `decision-badge ${decision.cls}`;
    byId("human-channel").textContent = message ? channelLabel(message.channel) : (action?.type === "create_call_task" ? "Human phone call" : "No automated message");
    byId("human-send-at").textContent = message ? formatSendAt(message.send_at) : "Not scheduled";
    byId("human-next-action").textContent = actionLabel(action);

    const preview = byId("message-preview");
    const noMessage = byId("no-message");
    preview.hidden = !message;
    noMessage.hidden = Boolean(message);
    if (message) {
      byId("human-result-title").textContent = message.channel === "email" ? "Email to send" : "Text message to send";
      const subjectRow = byId("human-subject-row");
      subjectRow.hidden = !message.subject;
      byId("human-subject").textContent = message.subject || "";
      byId("human-body").textContent = message.body;
      const cta = ctaLabel(message.cta);
      byId("human-cta").hidden = !cta;
      byId("human-cta").textContent = cta;
    } else {
      byId("human-result-title").textContent = "Human decision";
      byId("no-message-title").textContent = noMessageTitle(action);
      byId("no-message-reason").textContent = action?.reason ? sentence(action.reason) : actionLabel(action);
    }

    if (message && diagnostics.engine === "model") {
      byId("human-engine-note").textContent = "AI wrote the wording. The safety rules checked it before showing this result.";
    } else if (message) {
      byId("human-engine-note").textContent = "A validated template wrote the wording. No live AI model was used for this result.";
    } else {
      byId("human-engine-note").textContent = "The safety rules made this decision. No wording model was needed.";
    }
  }

  function checkRows(diagnostics) {
    const evaluation = diagnostics.evaluation || {};
    const groups = [
      ["Required state", evaluation.required_states || []],
      ["Constraint", evaluation.constraints || []],
      ["Threshold", evaluation.thresholds || []],
    ];
    const rows = [];
    groups.forEach(([kind, items]) => items.forEach((item) => {
      const mark = statusMark(item.status);
      let detail = item.status;
      if (Object.prototype.hasOwnProperty.call(item, "actual")) {
        detail = `${item.actual ?? "not measured"} / ${item.target ?? item.expected ?? "required"}`;
      }
      rows.push(`<div class="check-row" data-status="${escapeHtml(item.status)}">
        <span class="check-icon ${escapeHtml(mark.cls)}" aria-hidden="true">${mark.icon}</span>
        <span class="check-name"><strong>${kind}:</strong> ${escapeHtml(item.name)}</span>
        <span class="check-detail">${escapeHtml(detail)}</span>
      </div>`);
    }));
    return rows.join("") || `<div class="check-row" data-status="not_measured"><span class="check-icon not_measured">?</span><span class="check-name">No assertions or thresholds supplied</span><span class="check-detail">not measured</span></div>`;
  }

  function renderAnswerKey(answer, key) {
    const box = byId("answer-key");
    box.hidden = !key;
    if (!key) return;
    const got = answer.next_message;
    const want = key.next_message;
    const same = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
    const rows = [];
    if (!got || !want) {
      rows.push([!got === !want, `Send or not: expected ${want ? "a message" : "no message"}, got ${got ? "a message" : "no message"}`]);
    } else {
      rows.push([got.channel === want.channel, `Channel: expected ${channelLabel(want.channel)}, got ${channelLabel(got.channel)}`]);
      rows.push([got.send_at === want.send_at, `Time: expected ${formatSendAt(want.send_at)}, got ${formatSendAt(got.send_at)}`]);
      rows.push([!got.subject === !want.subject, `Subject: expected ${want.subject ? "a subject" : "none"}, got ${got.subject ? "a subject" : "none"}`]);
      rows.push([same(got.cta, want.cta), `Buttons or link: ${same(got.cta, want.cta) ? "match exactly" : "differ from the answer key"}`]);
    }
    rows.push([same(answer.next_action, key.next_action), `Next step: expected ${actionLabel(key.next_action)}, got ${actionLabel(answer.next_action)}`]);
    byId("answer-key-list").innerHTML = rows.map(([ok, text]) => `<li><span class="${ok ? "ok" : "bad"}" aria-label="${ok ? "match" : "mismatch"}">${ok ? "✓" : "✗"}</span><span>${escapeHtml(text)}</span></li>`).join("");
    byId("answer-key-body-row").hidden = !want?.body;
    byId("answer-key-body").textContent = want?.body || "";
  }

  function renderRecord(index) {
    state.active = index;
    const record = state.payload.records[index];
    const diagnostics = record.diagnostics;
    const answer = JSON.parse(record.submission_line);
    renderHumanAnswer(answer, diagnostics);
    renderAnswerKey(answer, record.answer_key);
    byId("submission-output").textContent = JSON.stringify(answer, null, 2);
    byId("byte-count").textContent = encoder.encode(oneBytes(index)).length;
    byId("record-state").textContent = `Record ${index + 1} of ${state.payload.record_count}`;
    byId("diagnostic-summary").innerHTML = [
      ["Task", diagnostics.task_id],
      ["Engine", diagnostics.engine],
      ["Latency", `${diagnostics.latency_ms} ms`],
      ["Fallback", diagnostics.fallback_reason || "none"],
    ].map(([label, value]) => `<div class="summary-item"><div class="summary-label">${label}</div><div class="summary-value">${escapeHtml(value)}</div></div>`).join("");

    const errors = diagnostics.errors || [];
    const errorBox = byId("record-errors");
    errorBox.hidden = errors.length === 0;
    errorBox.innerHTML = errors.length ? `<strong>This record has an error</strong><ul>${errors.map((error) => `<li>${escapeHtml(error)}</li>`).join("")}</ul>` : "";
    byId("check-list").innerHTML = checkRows(diagnostics);
    byId("decision-trail").innerHTML = (diagnostics.why || []).map((item) => `<article class="trail-item">
      <div class="trail-head"><span>${escapeHtml(item.rule)}</span><span>${escapeHtml(item.status)}</span></div>
      <p>${escapeHtml(item.plain_english)}</p>
      <small>${escapeHtml(item.confidence)} · ${escapeHtml(item.citation)}</small>
    </article>`).join("");
    document.querySelectorAll(".record-tab").forEach((tab, tabIndex) => tab.setAttribute("aria-selected", tabIndex === index ? "true" : "false"));
  }

  function renderBatch(payload) {
    state.payload = payload;
    state.active = 0;
    byId("empty-state").hidden = true;
    byId("results").hidden = false;
    byId("record-count").textContent = payload.record_count;
    byId("mode-label").textContent = payload.mode === "offline" ? "Template fallback result" : "AI writer result";
    byId("record-tabs").innerHTML = payload.records.map((record, index) => {
      const hasError = (record.diagnostics.errors || []).length > 0;
      const answer = JSON.parse(record.submission_line);
      const decision = decisionSummary(answer);
      return `<button type="button" class="record-tab${hasError ? " has-error" : ""}" role="tab" aria-selected="${index === 0}" data-index="${index}"><span>Record ${index + 1}</span><small>${escapeHtml(decision.label)}</small></button>`;
    }).join("");
    document.querySelectorAll(".record-tab").forEach((button) => button.addEventListener("click", () => renderRecord(Number(button.dataset.index))));
    renderRecord(0);
    byId("results").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function runBatch() {
    const error = byId("request-error");
    const button = byId("run-button");
    error.hidden = true;
    const jsonl = byId("jsonl-input").value;
    if (!jsonl.trim()) {
      error.textContent = "Paste or upload at least one JSON object.";
      error.hidden = false;
      byId("jsonl-input").focus();
      return;
    }
    button.disabled = true;
    button.textContent = "Running assignments";
    byId("workbench").classList.add("loading");
    try {
      const response = await fetch("/case-study/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jsonl, offline: byId("offline").checked }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || `Request failed with status ${response.status}`);
      if (!payload.record_count) throw new Error("The batch did not contain any records.");
      renderBatch(payload);
    } catch (cause) {
      error.textContent = cause.message || "The batch could not run.";
      error.hidden = false;
    } finally {
      button.disabled = false;
      button.textContent = "Run assignments";
      byId("workbench").classList.remove("loading");
    }
  }

  byId("run-button").addEventListener("click", runBatch);
  byId("copy-one").addEventListener("click", () => copyText(oneBytes(), "Copied one exact export line"));
  byId("copy-all").addEventListener("click", () => copyText(allBytes(), "Copied the complete JSONL export"));
  byId("download-all").addEventListener("click", () => downloadText(allBytes()));
  byId("file-input").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    byId("jsonl-input").value = await file.text();
    byId("file-name").textContent = file.name;
  });
  byId("offline").addEventListener("change", (event) => {
    byId("mode-label").textContent = event.target.checked ? "Template fallback ready" : "AI writer ready";
  });

  window.caseStudyDemo = { oneBytes, allBytes, renderBatch };
})();
