// PropertyStack shared shell -- plain JS, no framework, no build step.
// Every page calls renderShell(activeTab) then fetches its own data/*.json.

const NAV_TABS = [
  { key: "map", label: "Map", href: "map.html" },
  { key: "leads", label: "Leads", href: "index.html" },
  { key: "hood", label: "How it works", href: "under-the-hood.html" },
];


// The chat is its own app (Open WebUI, Google sign-in). Local trial on :3000,
// live URL on Railway.
// Tests override this via window.PS_CHAT_URL (see tooling/qa/check-panel.sh).
const CHAT_APP_URL = window.PS_CHAT_URL || (location.port === "8876"
  ? location.origin // isolated human preview: chat is behind the same front door
  : location.hostname === "localhost"
    ? "http://localhost:3000"
    : location.origin);  // live: same address as the site (site/Caddyfile)

// The public landing page (the marketing site). The human preview runs it on :8765.
const LANDING_URL = location.port === "8876" ? "http://localhost:8765" : "https://cranesignal.com";

// A Google sign-up's optional "What best describes you?" pick (chatbot/branding/
// loader.js) is sent to the signup list once, now that we know their email.
(function sendPendingRole() {
  let role;
  try { role = localStorage.getItem("cs-pending-role"); } catch (e) { return; }
  if (!role) return;
  fetch("/api/v1/auths/", { credentials: "include" })
    .then((r) => (r.ok ? r.json() : null))
    .then((me) => {
      if (!me || !me.email) return;
      localStorage.removeItem("cs-pending-role");
      fetch(LANDING_URL + "/api/signup", { method: "POST", mode: "no-cors", keepalive: true,
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "source=app&role=" + encodeURIComponent(role) + "&email=" + encodeURIComponent(me.email) });
    })
    .catch(() => {});
})();

function renderShell(activeKey) {
  const shell = document.getElementById("app-shell");

  const navHtml = NAV_TABS.map(
    (t) => `<a href="${t.href}" class="${t.key === activeKey ? "active" : ""}">${t.label}</a>`
  ).join("") + `<a href="#" class="nav-chat" data-chat-toggle title="Ask CraneSignal (free account)">Chat</a>`;

  shell.innerHTML = `
    <aside class="sidebar">
      <a class="wordmark" href="${LANDING_URL}" title="Back to the CraneSignal home page">CraneSignal</a>
      <nav>${navHtml}</nav>
      <div class="top-controls">
        <div id="last-updated" style="color: var(--text-dim); font-size: 11px;"></div>
        <a href="${LANDING_URL}" style="color: var(--text-dim); font-size: 11px;">&larr; Home page</a>
        <a href="privacy.html" style="color: var(--text-dim); font-size: 11px;">Privacy</a>
        <a href="#" id="sign-out-link" style="color: var(--text-dim); font-size: 11px; display: none;">Sign out</a>
      </div>
    </aside>
    <main class="main" id="page-content"></main>
    <a class="ask-fab" href="#" data-chat-toggle aria-label="Ask the CraneSignal agent">Ask</a>
    <!-- Phones: the agent is always on screen as a bar at the bottom; tapping it opens the agent. -->
    <button class="ask-bar" type="button" data-chat-toggle aria-label="Ask the CraneSignal agent">
      <span class="ask-bar-text">Ask the agent: who should I call?</span>
      <span class="ask-bar-go" aria-hidden="true">&rarr;</span>
    </button>
  `;

  showLastUpdated();
  if (window.initChatPanel) window.initChatPanel();
  if (window.wireSignOut) window.wireSignOut();
}


// "Last updated" = the lead snapshot date, never the site deploy date.
function formatDataDate(iso) {
  if (!iso) return "";
  const d = new Date(`${iso}T12:00:00`);
  if (isNaN(d)) return "";
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function formatUpdated(iso) {
  if (!iso) return "";
  const d = new Date(`${iso}T12:00:00`);
  if (isNaN(d)) return "";
  return `Last updated: ${d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
}

function summaryHero(summary) {
  if (!summary || !summary.lastCheck) {
    return "Buildings worth a call now. Being built. Opening soon. Just sold.";
  }
  const permits = Number(summary.permitsFiled || 0).toLocaleString("en-US");
  const sold = Number(summary.sold || 0).toLocaleString("en-US");
  const total = Number(summary.totalTracked || 0).toLocaleString("en-US");
  // "just filed" and "just sold" claimed the whole list was recent; most of
  // these buildings last moved over a year ago. State the size and the real
  // recent count separately, and let each lead carry its own date.
  const recent = Number(summary.recentLast180Days || 0).toLocaleString("en-US");
  const headline = `Last check ${formatDataDate(summary.lastCheck)}: ${total} buildings tracked — ${permits} being built or planned, ${sold} sold to a new owner.`;
  if (!summary.recentLast180Days) return headline;
  return `${headline} ${recent} with a permit or sale in the last 6 months.`;
}

function setLastUpdated(iso) {
  const el = document.getElementById("last-updated");
  if (el) el.textContent = formatUpdated(iso);
}

async function showLastUpdated() {
  try {
    const manifest = await loadData("data/areas/index.json");
    setLastUpdated(manifest.updated);
  } catch (e) {
    setLastUpdated("");
  }
}

async function loadData(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`failed to load ${path}: ${res.status}`);
  return res.json();
}

function scoreBadgeColor(score) {
  if (score >= 70) return "var(--score-high)";
  if (score >= 40) return "var(--score-mid)";
  return "var(--score-low)";
}

function vendorPill(vendor, colorMap) {
  if (!vendor) {
    return `<span class="pill" style="background:var(--paper-2);color:var(--muted);">No software yet</span>`;
  }
  const color = (colorMap && colorMap[vendor]) || "#5d6577";  // readable default on white
  return `<span class="pill" style="background:${color}22;color:${color};">${vendor}</span>`;
}

// Leads number boxes, from the rows currently shown (state + region + city + search).
// "Opening soon" = shown buildings, not sold, opening within the next 12 months.
function leadStats(rows, today) {
  const now = (today || new Date()).toISOString().slice(0, 10);
  const horizon = `${Number(now.slice(0, 4)) + 1}${now.slice(4)}`;
  return {
    leads: rows.length,
    newThisWeek: rows.filter((l) => l.isNew).length,
    unitsInPlay: rows.reduce((sum, l) => sum + (l.units || 0), 0),
    openingNext12mo: rows.filter((l) => l.signalType !== "Sold" && l.openingDate
      && l.openingDate > now && l.openingDate <= horizon).length,
  };
}

// Detail page for a lead row with no propertyId: find the lead by its own id.
// `areaFiles` = [{slug, label, leads}], the wanted area first when known.
function pickLead(areaFiles, id) {
  for (const a of areaFiles) {
    const lead = (a.leads || []).find((l) => l.id === id);
    if (lead) return { lead, area: a };
  }
  return null;
}

async function findLead(id, areaSlug) {
  const m = await loadData("data/areas/index.json");
  const areas = visibleAreas(m.areas).slice().sort((a, b) => (b.slug === areaSlug) - (a.slug === areaSlug));
  for (const a of areas) {
    const data = await loadData(a.dataPath);
    const hit = pickLead([{ slug: a.slug, label: a.label, leads: data.leads }], id);
    if (hit) return hit;
  }
  return null;
}

function placeholderBanner(statusText) {
  if (!statusText) return "";
  return `<div class="placeholder-banner">${statusText}</div>`;
}

// Filter out hidden areas (those with hidden: true in areas/index.json).
function visibleAreas(areas) {
  return (areas || []).filter((a) => !a.hidden);
}

// Leads: one button per area (5.2). `areas` is site/data/areas/index.json's
// `areas` list; `activeSlug` is the one currently shown; `onSelect(slug)` swaps data.
function renderAreaButtons(areas, activeSlug) {
  const visible = visibleAreas(areas);
  if (!visible || visible.length < 2) return "";
  return `<div class="area-buttons">${visible.map((a) => `
    <button type="button" class="area-btn ${a.slug === activeSlug ? "active" : ""}" data-area="${a.slug}">${a.label}</button>
  `).join("")}</div>`;
}

function wireAreaButtons(container, onSelect) {
  container.querySelectorAll(".area-btn").forEach((btn) => {
    btn.addEventListener("click", () => onSelect(btn.dataset.area));
  });
}

// One wording everywhere: the data files still say "software not picked yet".
function sameWords(text) {
  return String(text || "")
    .replace(/software not picked yet/gi, "no software yet")
    .replace(/software not chosen yet/gi, "no software yet")
    .replace(/not picked yet/gi, "no software yet")
    .replace(/not chosen yet/gi, "no software yet");
}
