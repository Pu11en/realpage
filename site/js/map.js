// US reach map: states from vendor/states-albers-10m.json (already projected to
// 975x610), dots from data/reach.json placed with the matching Albers USA projection.

(async function () {
  const svg = document.getElementById("us-map");
  const card = document.getElementById("map-card");
  const NS = "http://www.w3.org/2000/svg";
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const el = (tag, attrs) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  };

  const [us, reach] = await Promise.all([loadData("vendor/states-albers-10m.json"), loadData("data/reach.json")]);

  const statePath = d3.geoPath();
  const states = el("g", {});
  for (const f of topojson.feature(us, us.objects.states).features) {
    states.appendChild(el("path", { class: "state", d: statePath(f) }));
  }
  svg.appendChild(states);

  // Same projection us-atlas used for the *-albers-10m files.
  const project = d3.geoAlbersUsa().scale(1300).translate([487.5, 305]);
  const maxSigns = Math.max(1, ...reach.map((d) => d.signs || 0));
  const dots = el("g", {});
  // Big dots first so small ones stay clickable on top.
  const sorted = [...reach].sort((a, b) => (b.signs || 0) - (a.signs || 0));
  for (const d of sorted) {
    const xy = project([d.lon, d.lat]);
    if (!xy) continue;
    const [x, y] = xy;
    const g = el("g", { "data-dot": "", tabindex: "0", role: "button", "aria-label": `${d.city}, ${d.state}` });
    if (d.kind === "scout") {
      g.appendChild(el("rect", { class: "dot-scout", x: x - 6, y: y - 6, width: 12, height: 12, transform: `rotate(45 ${x} ${y})` }));
      const t = el("text", { class: "dot-label", x: x + 10, y: y + 3 });
      t.textContent = "researching";
      g.appendChild(t);
    } else {
      const r = 4 + 14 * Math.sqrt((d.signs || 0) / maxSigns);
      g.appendChild(el("circle", { class: "dot-reach", cx: x, cy: y, r }));
    }
    const title = el("title", {});
    title.textContent = `${d.city}, ${d.state}`;
    g.appendChild(title);
    const open = () => showCard(d, g);
    g.addEventListener("click", open);
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    dots.appendChild(g);
  }
  svg.appendChild(dots);

  function showCard(d, g) {
    svg.querySelectorAll("[data-dot].active").forEach((n) => n.classList.remove("active"));
    g.classList.add("active");
    const count = d.kind === "scout"
      ? "Researching this area"
      : `${d.signs} RealPage sign${d.signs === 1 ? "" : "s"}`;
    card.innerHTML = `
      <button class="close" aria-label="Close">&times;</button>
      <h3>${esc(d.city)}, ${esc(d.state)}</h3>
      <div class="count">${count}</div>
      ${d.note ? `<div class="meta">${esc(d.note)}</div>` : ""}
      <ul>${(d.links || []).map((l) => `<li><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.title)}</a></li>`).join("")}</ul>
    `;
    card.hidden = false;
    card.querySelector(".close").addEventListener("click", () => { card.hidden = true; g.classList.remove("active"); });
  }
})().catch((e) => {
  document.getElementById("page-content").insertAdjacentHTML("beforeend", `<div class="placeholder-banner">Map failed to load: ${e.message}</div>`);
  throw e;
});
