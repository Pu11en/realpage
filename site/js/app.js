// PropertyStack shared shell -- plain JS, no framework, no build step.
// Every page calls renderShell(activeTab) then fetches its own data/*.json.

const NAV_TABS = [
  { key: "leads", label: "Early Leads", href: "index.html" },
  { key: "table", label: "Master Table", href: "master-table.html" },
  { key: "share", label: "Software Share", href: "software-share.html" },
  { key: "hood", label: "Under the Hood", href: "under-the-hood.html" },
];

const VENDORS = ["RealPage", "Yardi", "Entrata", "Yotta", "AppFolio"];

function getViewAs() {
  return localStorage.getItem("propertystack.viewAs") || "Neutral";
}

function setViewAs(vendor) {
  localStorage.setItem("propertystack.viewAs", vendor);
  document.body.dataset.viewAs = vendor;
}

function renderShell(activeKey) {
  const shell = document.getElementById("app-shell");
  const viewAs = getViewAs();
  document.body.dataset.viewAs = viewAs;

  const navHtml = NAV_TABS.map(
    (t) => `<a href="${t.href}" class="${t.key === activeKey ? "active" : ""}">${t.label}</a>`
  ).join("");

  const vendorOptions = ["Neutral", ...VENDORS]
    .map((v) => `<option value="${v}" ${v === viewAs ? "selected" : ""}>${v}</option>`)
    .join("");

  shell.innerHTML = `
    <aside class="sidebar">
      <div class="wordmark">PropertyStack</div>
      <nav>${navHtml}</nav>
      <div class="top-controls">
        <select id="area-select">
          <option>Plano</option>
          <option>Richardson</option>
        </select>
        <select id="view-as-select">${vendorOptions}</select>
        <div style="color: var(--text-dim); font-size: 11px;">Last updated: Sep 10, 2026</div>
      </div>
    </aside>
    <main class="main" id="page-content"></main>
  `;

  document.getElementById("view-as-select").addEventListener("change", (e) => {
    setViewAs(e.target.value);
  });
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
    return `<span class="pill" style="background:#27272a;color:#a1a1aa;">Not chosen yet</span>`;
  }
  const color = (colorMap && colorMap[vendor]) || "#52525b";
  return `<span class="pill" style="background:${color}22;color:${color};">${vendor}</span>`;
}

function isDimmedRow(vendor) {
  const viewAs = getViewAs();
  if (viewAs === "Neutral") return false;
  return vendor === viewAs;
}

function placeholderBanner(statusText) {
  if (!statusText) return "";
  return `<div class="placeholder-banner">${statusText}</div>`;
}
