// Client map: states from vendor/states-albers-10m.json (already projected to 975x610),
// shaded by RealPage buildings found per state (data/client-map.json, built by build_data.py).

(async function () {
  const svg = document.getElementById("us-map");
  const tip = document.getElementById("map-tip");
  const NS = "http://www.w3.org/2000/svg";
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const [us, data, markerData] = await Promise.all([
    loadData("vendor/states-albers-10m.json"),
    loadData("data/client-map.json"),
    loadData("data/map-markers.json").catch(() => ({ markers: [] })),
  ]);
  const markers = Object.fromEntries(markerData.markers.map((m) => [m.state, m]));
  const centers = {};
  const max = Math.max(1, ...Object.values(data.states).map((s) => s.total));
  const path = d3.geoPath();

  for (const f of topojson.feature(us, us.objects.states).features) {
    const name = f.properties.name;
    const s = data.states[name];
    const p = document.createElementNS(NS, "path");
    p.setAttribute("class", "state");
    p.setAttribute("d", path(f));
    p.setAttribute("data-state", name);
    if (s) {
      p.setAttribute("data-count", s.total);
      // sqrt keeps small counts visible next to the big states
      p.style.fill = `rgba(26, 61, 143, ${(0.12 + 0.88 * Math.sqrt(s.total / max)).toFixed(3)})`;
    }
    p.addEventListener("mousemove", (e) => showTip(e, name, s));
    p.addEventListener("mouseleave", () => { tip.hidden = true; });
    svg.appendChild(p);
    centers[name] = path.centroid(f);
  }

  // Amber markers: states we have leads in. One click opens that state's table.
  for (const m of Object.values(markers)) {
    const c = centers[m.state];
    if (!c || Number.isNaN(c[0])) continue;
    const g = document.createElementNS(NS, "g");
    g.setAttribute("class", "lead-marker");
    g.setAttribute("transform", `translate(${c[0]},${c[1]})`);
    g.setAttribute("tabindex", "0");
    g.setAttribute("role", "link");
    g.setAttribute("aria-label", `${m.label}: open the table`);
    g.innerHTML = `<circle r="9"></circle><text y="-14" text-anchor="middle">${esc(m.label)}</text>`;
    g.addEventListener("mousemove", (e) => showMarkerTip(e, m));
    g.addEventListener("mouseleave", () => { tip.hidden = true; });
    g.addEventListener("click", () => { location.href = m.link; });
    g.addEventListener("keydown", (e) => { if (e.key === "Enter") location.href = m.link; });
    svg.appendChild(g);
  }

  function showMarkerTip(e, m) {
    tip.innerHTML = `<strong>${esc(m.state)}</strong><div class="count lead-count">${m.leads} lead${m.leads === 1 ? "" : "s"}</div>
      <ul>${m.topCities.map((c) => `<li>${esc(c)}</li>`).join("")}</ul><div class="hint">Click to open the table</div>`;
    place(e);
  }

  function place(e) {
    const box = svg.parentElement.getBoundingClientRect();
    tip.style.left = `${e.clientX - box.left + 14}px`;
    tip.style.top = `${e.clientY - box.top + 14}px`;
    tip.hidden = false;
  }

  function showTip(e, name, s) {
    tip.innerHTML = s
      ? `<strong>${esc(name)}</strong><div class="count">${s.total} RealPage building${s.total === 1 ? "" : "s"}</div>
         <ul>${s.topCities.map((c) => `<li>${esc(c.city)}: ${c.count}</li>`).join("")}</ul>`
      : `<strong>${esc(name)}</strong><div>None found (not searched or no hits)</div>`;
    const box = svg.parentElement.getBoundingClientRect();
    tip.style.left = `${e.clientX - box.left + 14}px`;
    tip.style.top = `${e.clientY - box.top + 14}px`;
    tip.hidden = false;
  }
})().catch((e) => {
  document.getElementById("page-content").insertAdjacentHTML("beforeend", `<div class="placeholder-banner">Map failed to load: ${e.message}</div>`);
  throw e;
});
