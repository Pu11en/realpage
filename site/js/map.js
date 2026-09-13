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
  // Building dots stack up at country scale, so draw one dot per area (at the middle of its
  // buildings, sized by count); the card lists every proven RealPage building there.
  const areas = {};
  for (const b of reach.filter((d) => d.kind === "building")) {
    const a = (areas[b.area] ||= { kind: "area", area: b.area, buildings: [], lat: 0, lon: 0, n: 0 });
    a.buildings.push(b);
    if (b.lat != null) { a.lat += b.lat; a.lon += b.lon; a.n += 1; }
  }
  const points = Object.values(areas).filter((a) => a.n).map((a) => ({ ...a, lat: a.lat / a.n, lon: a.lon / a.n }));
  points.push(...reach.filter((d) => d.kind === "scout"));
  const maxCount = Math.max(1, ...points.map((d) => (d.buildings || []).length));
  const dots = el("g", {});
  for (const d of points) {
    const xy = project([d.lon, d.lat]);
    if (!xy) continue;
    const [x, y] = xy;
    const label = d.kind === "scout" ? `${d.city}, ${d.state}` : areaName(d);
    const g = el("g", { "data-dot": "", tabindex: "0", role: "button", "aria-label": label });
    if (d.kind === "scout") {
      g.appendChild(el("rect", { class: "dot-scout", x: x - 6, y: y - 6, width: 12, height: 12, transform: `rotate(45 ${x} ${y})` }));
      const t = el("text", { class: "dot-label", x: x + 10, y: y + 3 });
      t.textContent = "researching";
      g.appendChild(t);
    } else {
      const r = 5 + 13 * Math.sqrt(d.buildings.length / maxCount);
      g.appendChild(el("circle", { class: "dot-reach", cx: x, cy: y, r }));
    }
    const title = el("title", {});
    title.textContent = label;
    g.appendChild(title);
    const open = () => showCard(d, g);
    g.addEventListener("click", open);
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    dots.appendChild(g);
  }
  svg.appendChild(dots);

  function areaName(a) {
    const cities = [...new Set(a.buildings.map((b) => b.city))];
    return `${cities.join(" & ")}, ${a.buildings[0].state}`;
  }

  function showCard(d, g) {
    svg.querySelectorAll("[data-dot].active").forEach((n) => n.classList.remove("active"));
    g.classList.add("active");
    let body;
    if (d.kind === "scout") {
      body = `<h3>${esc(d.city)}, ${esc(d.state)}</h3><div class="count">The scout is researching this area</div>
        <ul>${(d.links || []).map((l) => `<li><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.title)}</a></li>`).join("")}</ul>`;
    } else {
      const list = [...d.buildings].sort((a, b) => b.units - a.units);
      body = `<h3>${esc(areaName(d))}</h3>
        <div class="count">${list.length} apartment building${list.length === 1 ? "" : "s"} proven to run RealPage</div>
        <ul>${list.map((b) => `<li><strong>${esc(b.name)}</strong> · ${esc(b.city)} · ${b.units} units ·
          <a href="${esc(b.links[0].url)}" target="_blank" rel="noopener">proof</a></li>`).join("")}</ul>`;
    }
    card.innerHTML = `<button class="close" aria-label="Close">&times;</button>${body}`;
    card.hidden = false;
    card.querySelector(".close").addEventListener("click", () => { card.hidden = true; g.classList.remove("active"); });
  }
})().catch((e) => {
  document.getElementById("page-content").insertAdjacentHTML("beforeend", `<div class="placeholder-banner">Map failed to load: ${e.message}</div>`);
  throw e;
});
