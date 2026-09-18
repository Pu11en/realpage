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

  function renderRecord(index) {
    state.active = index;
    const record = state.payload.records[index];
    const diagnostics = record.diagnostics;
    byId("submission-output").textContent = JSON.stringify(JSON.parse(record.submission_line), null, 2);
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
    byId("mode-label").textContent = payload.mode === "offline" ? "Offline result" : "Configured writer";
    byId("record-tabs").innerHTML = payload.records.map((record, index) => {
      const hasError = (record.diagnostics.errors || []).length > 0;
      return `<button type="button" class="record-tab${hasError ? " has-error" : ""}" role="tab" aria-selected="${index === 0}" data-index="${index}">Record ${index + 1}</button>`;
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
    byId("mode-label").textContent = event.target.checked ? "Offline ready" : "Configured writer ready";
  });

  window.caseStudyDemo = { oneBytes, allBytes, renderBatch };
})();
