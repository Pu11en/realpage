// Client map: states from vendor/states-albers-10m.json (already projected to 975x610),
// shaded by RealPage buildings found per state (data/client-map.json, built by build_data.py).

(async function () {
  const svg = document.getElementById("us-map");
  const tip = document.getElementById("map-tip");
  const NS = "http://www.w3.org/2000/svg";
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const [us, data] = await Promise.all([loadData("vendor/states-albers-10m.json"), loadData("data/client-map.json")]);
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
      p.style.fill = `rgba(34, 197, 94, ${(0.15 + 0.85 * Math.sqrt(s.total / max)).toFixed(3)})`;
    }
    p.addEventListener("mousemove", (e) => showTip(e, name, s));
    p.addEventListener("mouseleave", () => { tip.hidden = true; });
    svg.appendChild(p);
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
