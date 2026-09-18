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
    if (status === "not_applicable") return { icon: "–", cls: "not_applicable" };
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
      let detail = words(item.status);
      if (item.status === "not_applicable") {
        detail = "does not apply";
      } else if (Object.prototype.hasOwnProperty.call(item, "actual")) {
        const unit = item.name === "p95_latency_ms" ? " ms" : "";
        detail = `${item.actual ?? "not measured"}${item.actual == null ? "" : unit} / target ${item.target ?? item.expected ?? "required"}${unit}`;
      }
      const note = item.note ? `<small class="check-note">${escapeHtml(item.note)}</small>` : "";
      rows.push(`<div class="check-row" data-status="${escapeHtml(item.status)}">
        <span class="check-icon ${escapeHtml(mark.cls)}" aria-hidden="true">${mark.icon}</span>
        <span class="check-name"><strong>${kind}:</strong> ${escapeHtml(item.name)}${note}</span>
        <span class="check-detail">${escapeHtml(detail)}</span>
      </div>`);
    }));
    return rows.join("") || `<div class="check-row" data-status="not_measured"><span class="check-icon not_measured">?</span><span class="check-name">No assertions or thresholds supplied</span><span class="check-detail">not measured</span></div>`;
  }

  function renderInput(line) {
    const grid = byId("input-grid");
    const note = byId("input-raw-note");
    let raw = null;
    try { raw = JSON.parse(line); } catch (_) { raw = null; }
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
      grid.innerHTML = "";
      note.hidden = false;
      note.textContent = line.trim() ? `This line is not a valid record, so it could not be read: ${line.slice(0, 200)}` : "This line is empty.";
      return;
    }
    note.hidden = true;
    const input = raw.input && typeof raw.input === "object" ? raw.input : {};
    const profile = input.profile && typeof input.profile === "object" ? input.profile : {};
    const consent = raw.consent && typeof raw.consent === "object" ? raw.consent : {};
    const yesNo = (v) => v === true ? "Yes" : v === false ? "No" : "Not given";
    const names = { sms: "Text", email: "Email", voice: "Phone" };
    const list = (v) => Array.isArray(v) && v.length ? v.map((x) => names[x] || words(x)).join(" → ") : "None given";
    const date = (v) => { const d = new Date(v); return v && !isNaN(d) ? d.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }) + " UTC" : (v || "Not given"); };
    const known = new Set(["first_name", "amenity_interest", "city_interest", "amenities", "preferred_name"]);
    const other = Object.keys(profile).filter((k) => !known.has(k));
    const rows = [
      ["Customer", profile.first_name ? String(profile.first_name) : "No first name"],
      ["Type", [raw.persona, raw.lifecycle_stage].filter(Boolean).map(words).join(", ") || "Not given"],
      ["Property", input.property_name || "Not given"],
      ["Allowed to text?", yesNo(consent.sms_opt_in)],
      ["Allowed to email?", yesNo(consent.email_opt_in)],
      ["Allowed to call?", yesNo(consent.voice_opt_in)],
      ["Preferred order", list(raw.channel_preferences)],
      ["Target move date", input.move_date_target || "Not given"],
      ["Last contact", date(input.last_interaction)],
      ["Customer's time zone", input.timezone || "Not given"],
      ["Language", input.language || "Not given"],
    ];
    if (Array.isArray(profile.amenity_interest)) rows.push(["Interested in", profile.amenity_interest.map(words).join(", ")]);
    if (profile.city_interest) rows.push(["Looking in", String(profile.city_interest)]);
    const reply = input.inbound_reply || raw.inbound_reply;
    if (reply) rows.push(["Customer replied", `"${reply}"`, true]);
    const prior = input.prior_options || raw.prior_options;
    if (Array.isArray(prior)) rows.push(["Options they were offered", prior.map((o, i) => `${i + 1} = ${o}`).join(", ")]);
    if (other.length) rows.push(["Other profile details", other.map((k) => `${words(k)}: ${typeof profile[k] === "object" ? JSON.stringify(profile[k]) : profile[k]}`).join("; ") + " (never shown to the AI)", true]);
    if (raw.expected) rows.push(["Answer key included", "Yes, used only to grade the result afterwards"]);
    grid.innerHTML = rows.map(([label, value, flag]) => `<div${flag ? ' class="flag"' : ""}><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("");
  }

  function codeLink(code) {
    if (!code || !state.payload?.code_base) return "";
    const [file, line] = code.split(":");
    return `<a href="${escapeHtml(state.payload.code_base + file)}#L${escapeHtml(line)}" target="_blank" rel="noopener">${escapeHtml(code)} ↗</a>`;
  }

  function renderCodeTrail(diagnostics) {
    const steps = (diagnostics.why || []).filter((item) => item.status !== "skipped" && item.code);
    byId("code-steps").innerHTML = steps.map((item) => `<li class="st-${escapeHtml(item.status)}"><span class="rule">${escapeHtml(words(item.rule))}</span>: ${escapeHtml(sentence(item.plain_english))}${codeLink(item.code)}</li>`).join("")
      || "<li>No rule steps were recorded for this line.</li>";
  }

  function renderAiProcess(answer, diagnostics) {
    const trail = diagnostics.why || [];
    const find = (rule) => trail.find((item) => item.rule === rule);
    const request = find("writer.request");
    const reply = find("writer.reply");
    const fallback = find("writer.fallback");
    const final = find("writer");
    const message = answer.next_message;
    const pre = (text) => `<pre>${escapeHtml(text)}</pre>`;
    const steps = [];
    steps.push(["Rules decided first, without the AI",
      message ? `${channelLabel(message.channel)}, ${formatSendAt(message.send_at)}, next step: ${actionLabel(answer.next_action)}. The AI cannot change any of these.`
              : `No automated message. Next step: ${actionLabel(answer.next_action)}. The AI was not asked to write anything.`]);
    if (request) {
      const d = request.details || {};
      steps.push(["AI settings", `Model ${d.model}, temperature ${d.temperature} (no randomness), JSON-only reply, at most ${d.max_tokens} tokens, time limit ${d.timeout_ms} ms, one try with no retries.`, codeLink(request.code)]);
      const prompt = d.prompt || [];
      const system = prompt.find((m) => m.role === "system");
      const user = prompt.find((m) => m.role === "user");
      if (system) steps.push(["Instructions sent to the AI", "The fixed rules every record gets." + pre(system.content)]);
      if (user) {
        let input = user.content;
        try { input = JSON.stringify(JSON.parse(user.content.replace(/^Input \(JSON\):\n/, "")), null, 2); } catch (_) { /* show as sent */ }
        steps.push(["Record details sent to the AI", "Only approved fields. The answer key and any sensitive profile details are never sent." + pre(input)]);
      }
      steps.push(["AI replied", `${Math.round(d.latency_ms)} ms.` + (reply ? pre(reply.details?.raw ?? "(empty)") : "")]);
    } else if (fallback) {
      steps.push(["AI not called", sentence(fallback.details?.reason || fallback.plain_english)]);
    } else {
      steps.push(["AI not needed", "The rules made the whole decision, so no wording was written."]);
    }
    if (final && diagnostics.engine === "model") {
      steps.push(["Safety check passed", "Code checked the AI's wording: opt-out line, subject rules, the exact buttons or link, length, fair-housing words and no personal details. The AI's wording was used."]);
    } else if (request && fallback) {
      steps.push(["Safety check rejected the AI's wording", `${sentence(fallback.details?.reason || "")} ${fallback.details?.error ? fallback.details.error + "." : ""} A pre-checked template was used instead.`]);
    }
    steps.push(["Total time", `${diagnostics.latency_ms} ms for this record.`]);
    byId("ai-steps").innerHTML = steps.map(([title, body, link]) => `<li><strong>${escapeHtml(title)}</strong>${link ? " " + link : ""}<p>${body.includes("<pre>") ? escapeHtml(body.split("<pre>")[0]) + "<pre>" + body.split("<pre>").slice(1).join("<pre>") : escapeHtml(body)}</p></li>`).join("");
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
    renderInput(record.input_line || "");
    renderCodeTrail(diagnostics);
    renderAiProcess(answer, diagnostics);
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
      <small>${escapeHtml(item.confidence)} · ${escapeHtml(item.citation)} ${codeLink(item.code)}</small>
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
  [["load-practice", "practice-12.jsonl", "Practice set 1"], ["load-practice-2", "practice-12b.jsonl", "Practice set 2"]].forEach(([id, file, label]) => {
    byId(id).addEventListener("click", async () => {
      const response = await fetch(`/case-study/assets/${file}`);
      byId("jsonl-input").value = await response.text();
      byId("file-name").textContent = `${label} loaded (12 records)`;
    });
  });

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
