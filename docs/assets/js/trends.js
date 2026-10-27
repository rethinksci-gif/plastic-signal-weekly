/* Signal Trends dashboard. Reads data/trends.json (built by scripts/build_trends.py). */
(function () {
  const script = document.currentScript;
  const SRC = script.dataset.src;
  const BASE = script.dataset.base || "/";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const fmt = new Intl.NumberFormat("en");
  const shortDate = (iso) => new Date(iso + "T12:00:00Z").toLocaleDateString("en-GB", { day: "2-digit", month: "short" });

  let D, lens = "drivers", filter = null, query = "", shown = 25;

  fetch(SRC, { cache: "no-cache" })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((data) => { D = data; prepare(); renderAll(); })
    .catch(() => {
      $("trend-kpis").innerHTML = '<div class="kpi"><span class="kpi-label">Trend data unavailable</span><span class="kpi-note">It is rebuilt with each weekly issue.</span></div>';
    });

  function prepare() {
    const ix = Object.fromEntries(D.issues.map((i) => [i.date, i]));
    D.items.forEach((it, n) => {
      it._id = n;
      it._issue = ix[it.issue];
      it._hay = [it.title, it.source, it.summary, it.pillar_name, ...(it.tags || []), ...(it.themes || []), ...(it.regions || [])].join(" ").toLowerCase();
    });
    const seen = D.issues.map((i) => i.signals_seen || 0).filter(Boolean).sort((a, b) => a - b);
    const median = seen.length ? seen[Math.floor(seen.length / 2)] : 0;
    D._low = new Set(D.issues.filter((i) => i.signals_seen && i.signals_seen < median * 0.4).map((i) => i.date));
    // Pillar rows built here so every lens shares one shape.
    D._pillarRows = D.pillars.map((p) => rowStats(p.name, p.by_week, (it) => it.pillar_name === p.name));
  }

  function rowStats(name, by_week, test) {
    const hits = D.items.filter(test);
    const sc = hits.map((h) => h.score).filter((s) => s != null);
    return { name, by_week, count: hits.length, avg_score: sc.length ? sc.reduce((a, b) => a + b, 0) / sc.length : null };
  }

  const LENSES = {
    drivers: { rows: () => D.drivers, test: (n) => (it) => it.themes.includes("Driver: " + n), label: "Driver" },
    polymers: { rows: () => D.polymers, test: (n) => (it) => it.themes.includes("Polymer: " + n), label: "Polymer" },
    pillars: { rows: () => D._pillarRows, test: (n) => (it) => it.pillar_name === n, label: "Pillar" },
    regions: { rows: () => D.regions, test: (n) => (it) => it.regions.includes(n), label: "Region" },
  };

  function renderAll() {
    renderCaveat(); renderKpis(); renderMomentum(); renderHeatmap(); renderBars(); renderHigh(); renderExplorer();
    $("generated").textContent = "Last rebuilt " + new Date(D.generated_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" }) + ".";
    wire();
  }

  function renderCaveat() {
    const n = D.issues.length, el = $("trend-caveat"), bits = [];
    if (n < 8) bits.push(`<strong>Early read:</strong> ${n} weekly issues so far. Treat movement here as a lead to check, not an established trend.`);
    if (D._low.size) bits.push(`The ${[...D._low].map(shortDate).join(", ")} issue drew on far fewer raw signals than usual, so it is shown faded.`);
    if (bits.length) { el.innerHTML = bits.join(" "); el.hidden = false; }
  }

  function renderKpis() {
    const t = D.totals;
    const tiles = [
      ["Issues", fmt.format(t.issues), `${shortDate(D.weeks[0])} – ${shortDate(D.weeks[D.weeks.length - 1])}`],
      ["Signals scanned", fmt.format(t.signals_seen), "raw items before filtering"],
      ["Decision items", fmt.format(t.items), `${Math.round((t.items / Math.max(t.signals_seen, 1)) * 100)}% kept`],
      ["Average score", t.avg_score != null ? t.avg_score.toFixed(1) : "–", "out of 10"],
      ["High signal", fmt.format(t.high_signal), "items scored 6+"],
    ];
    $("trend-kpis").innerHTML = tiles.map(([l, v, n]) => `<div class="kpi"><span class="kpi-label">${l}</span><span class="kpi-value">${v}</span><span class="kpi-note">${n}</span></div>`).join("");
  }

  function renderMomentum() {
    const window = 2;
    if (D.weeks.length < window + 1) { $("momentum").innerHTML = '<p class="momentum-empty">Momentum appears once there are at least three issues.</p>'; return; }
    const recentN = D.issues.slice(-window).reduce((a, i) => a + i.items_kept, 0);
    const earlierN = D.issues.slice(0, -window).reduce((a, i) => a + i.items_kept, 0);
    const pool = [
      ...(D.theme_momentum.Driver || []).map((r) => ({ ...r, kind: "Driver", lens: "drivers" })),
      ...(D.theme_momentum.Polymer || []).map((r) => ({ ...r, kind: "Polymer", lens: "polymers" })),
    ];
    const up = pool.filter((r) => r.delta > 0 && r.recent >= 2).sort((a, b) => b.delta - a.delta).slice(0, 5);
    const down = pool.filter((r) => r.delta < 0 && r.earlier >= 3).sort((a, b) => a.delta - b.delta).slice(0, 5);
    const row = (r, dir) => `<div class="momentum-row ${dir}">
        <span class="arrow" aria-label="${dir === "up" ? "rising" : "cooling"}"></span>
        <span class="momentum-name"><button class="chip-link" data-lens="${r.lens}" data-name="${esc(r.name)}" style="all:unset;cursor:pointer">${esc(r.name)}</button>
          <small>${r.kind} · ${r.recent} of ${recentN} recent items vs ${r.earlier} of ${earlierN} before</small></span>
        <span class="momentum-delta">${dir === "up" ? "<mark>" : ""}${r.delta > 0 ? "+" : "−"}${Math.abs(r.delta * 100).toFixed(1)} pts${dir === "up" ? "</mark>" : ""}</span>
      </div>`;
    $("moving-note").textContent = `Share of items in the latest ${window} issues versus the ${D.weeks.length - window} before.`;
    $("momentum").innerHTML =
      `<div class="momentum-col"><h3>Rising</h3>${up.map((r) => row(r, "up")).join("") || '<p class="momentum-empty">Nothing clearly rising.</p>'}</div>` +
      `<div class="momentum-col"><h3>Cooling</h3>${down.map((r) => row(r, "down")).join("") || '<p class="momentum-empty">Nothing clearly cooling.</p>'}</div>`;
  }

  function heatStyle(v, max) {
    if (!v) return "";
    const a = 0.12 + 0.83 * (v / max);
    return `background:rgba(var(--heat),${a.toFixed(3)});color:${a > 0.5 ? "var(--heat-on)" : "var(--ink)"}`;
  }

  function renderHeatmap() {
    const L = LENSES[lens], rows = L.rows();
    const max = Math.max(1, ...rows.flatMap((r) => r.by_week));
    const lowCls = (w) => (D._low.has(w) ? ' class="low-coverage"' : "");
    const head = `<thead><tr><th class="row-head" scope="col"><span class="visually-hidden">${L.label}</span></th>${D.weeks.map((w) => `<th scope="col"${lowCls(w)}>${shortDate(w)}</th>`).join("")}<th scope="col">Total</th><th scope="col">Avg score</th></tr></thead>`;
    const body = rows.map((r) => {
      const sel = filter && filter.lens === lens && filter.name === r.name;
      const cells = r.by_week.map((v, i) => {
        const w = D.weeks[i], low = D._low.has(w) ? " low-coverage" : "";
        return `<td class="${v ? "" : "zero"}${low}" style="${heatStyle(v, max)}" data-row="${esc(r.name)}" data-week="${w}" data-v="${v}">${v}</td>`;
      }).join("");
      return `<tr${sel ? ' class="selected"' : ""}><th class="row-head" scope="row"><button type="button" data-lens="${lens}" data-name="${esc(r.name)}">${esc(r.name)}</button></th>${cells}<td class="total">${r.count}</td><td class="score">${r.avg_score != null ? Number(r.avg_score).toFixed(1) : "–"}</td></tr>`;
    }).join("");
    $("heatmap").innerHTML = `<caption class="visually-hidden">${L.label} by issue, item counts</caption>${head}<tbody>${body}</tbody>`;
    const steps = document.querySelectorAll(".heat-legend i");
    steps.forEach((el, i) => { el.style.cssText = heatStyle(Math.round(((i + 1) / steps.length) * max) || 1, max); });
    $("heat-max").textContent = max;
  }

  function bars(el, rows, lensKey, accentFirst) {
    const max = Math.max(1, ...rows.map((r) => r.count));
    el.innerHTML = rows.map((r, i) => {
      const name = lensKey ? `<button type="button" data-lens="${lensKey}" data-name="${esc(r.name)}">${esc(r.name)}</button>` : esc(r.name);
      return `<div class="bar-row"><span>${name}</span><span class="bar-track"><span class="bar${accentFirst && i === 0 ? " accent" : ""}" style="width:${(r.count / max) * 82}%"></span><span class="bar-value">${r.count}${r.pct != null ? ` · ${r.pct}%` : ""}</span></span></div>`;
    }).join("");
  }

  function renderBars() {
    const withRegion = D.items.filter((i) => i.regions.length).length;
    bars($("regions"), D.regions.slice(0, 10), "regions");
    const tot = D.actions.reduce((a, r) => a + r.count, 0) || 1;
    const acts = D.actions.map((r) => ({ ...r, pct: Math.round((r.count / tot) * 100) }));
    bars($("actions"), acts, null, true);
    const top = acts[0];
    if (top) $("action-note").textContent = `${top.pct}% of items close with “${top.name.toLowerCase()}” — a read on how often the underlying evidence was thin.`;
    $("regions").insertAdjacentHTML("afterend", `<p class="trend-sub" style="margin-top:14px">${D.items.length - withRegion} items name no place.</p>`);
  }

  function issueLink(it) {
    return it._issue ? `${BASE}${it._issue.url}#item-${it.pillar}-${it.rank}` : null;
  }

  function chips(it) {
    const t = it.themes.map((th) => { const [k, n] = th.split(": "); return { lens: k === "Driver" ? "drivers" : "polymers", n }; });
    return `<div class="chips">${t.map((c) => `<button type="button" class="chip" data-lens="${c.lens}" data-name="${esc(c.n)}">${esc(c.n)}</button>`).join("")}</div>`;
  }

  function renderHigh() {
    const list = [...D.high_signal].sort((a, b) => b.score - a.score || b.issue.localeCompare(a.issue));
    $("high-cards").innerHTML = list.map((it) => {
      const s = it.summary && it.summary.length > 170 ? it.summary.slice(0, 168).replace(/\s+\S*$/, "") + "…" : it.summary || "";
      const il = issueLink(it);
      return `<article class="signal-card">
        <div class="meta"><span>${shortDate(it.issue)} · ${esc(it.pillar_name)}</span><span class="score">${it.score.toFixed(1)}</span></div>
        <h3><a href="${esc(it.url)}" rel="noopener" target="_blank">${esc(it.title)}</a></h3>
        <p>${esc(s)}${il ? ` <a href="${il}">In the issue →</a>` : ""}</p>
        ${chips(it)}
      </article>`;
    }).join("");
  }

  function filtered() {
    let list = D.items;
    if (filter) list = list.filter(LENSES[filter.lens].test(filter.name));
    if (query) { const q = query.toLowerCase().split(/\s+/).filter(Boolean); list = list.filter((it) => q.every((w) => it._hay.includes(w))); }
    return [...list].sort((a, b) => b.issue.localeCompare(a.issue) || (b.score || 0) - (a.score || 0));
  }

  function renderExplorer() {
    const list = filtered();
    $("explorer-count").textContent = `${list.length} of ${D.items.length} items`;
    const af = $("active-filter");
    if (filter) { af.hidden = false; af.querySelector("span").textContent = `${LENSES[filter.lens].label}: ${filter.name}`; } else af.hidden = true;
    const rows = list.slice(0, shown).map((it) => {
      const il = issueLink(it);
      return `<li class="item-row">
        <span class="item-date">${shortDate(it.issue)}</span>
        <div class="item-main"><a class="item-title" href="${esc(it.url)}" rel="noopener" target="_blank">${esc(it.title)}</a>
          <div class="item-sub">${esc(it.pillar_name)} · ${esc(it.source || "")}${il ? ` · <a href="${il}">in the issue</a>` : ""}</div>${chips(it)}</div>
        <span class="item-score">${it.score != null ? it.score.toFixed(1) : "–"}</span>
      </li>`;
    }).join("");
    $("item-list").innerHTML = rows || '<li class="item-row"><span></span><div class="item-main">No items match.</div></li>';
    const old = document.querySelector(".item-more"); if (old) old.remove();
    if (list.length > shown) $("item-list").insertAdjacentHTML("afterend", `<button type="button" class="item-more">Show ${Math.min(25, list.length - shown)} more</button>`);
  }

  function setFilter(lensKey, name) {
    filter = filter && filter.lens === lensKey && filter.name === name ? null : { lens: lensKey, name };
    shown = 25; renderExplorer(); renderHeatmap();
  }

  function wire() {
    $("lens-switch").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-lens]"); if (!b) return;
      lens = b.dataset.lens;
      document.querySelectorAll("#lens-switch button").forEach((x) => x.setAttribute("aria-selected", String(x === b)));
      renderHeatmap();
    });
    document.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-lens][data-name]"); if (!b) return;
      setFilter(b.dataset.lens, b.dataset.name);
      if (!b.closest("#explorer")) $("explorer").scrollIntoView({ behavior: "smooth" });
    });
    document.addEventListener("click", (e) => { if (e.target.closest(".item-more")) { shown += 25; renderExplorer(); } });
    $("active-filter").querySelector("button").addEventListener("click", () => { filter = null; renderExplorer(); renderHeatmap(); });
    let t; $("explorer-search").addEventListener("input", (e) => { clearTimeout(t); t = setTimeout(() => { query = e.target.value.trim(); shown = 25; renderExplorer(); }, 120); });

    const tip = $("trend-tip");
    const table = $("heatmap");
    table.addEventListener("pointermove", (e) => {
      const td = e.target.closest("td[data-week]");
      if (!td) { tip.hidden = true; return; }
      const v = +td.dataset.v, name = td.dataset.row, w = td.dataset.week;
      const hits = D.items.filter((it) => it.issue === w && LENSES[lens].test(name)(it)).sort((a, b) => (b.score || 0) - (a.score || 0));
      tip.innerHTML = `<b>${esc(name)}</b>${shortDate(w)} issue · ${v} item${v === 1 ? "" : "s"}${D._low.has(w) ? " · low-coverage week" : ""}` +
        (hits.length ? `<ul>${hits.slice(0, 3).map((h) => `<li>${esc(h.title)}</li>`).join("")}</ul>${hits.length > 3 ? `+${hits.length - 3} more` : ""}` : "");
      tip.hidden = false;
      const pad = 14, r = tip.getBoundingClientRect();
      let x = e.clientX + pad, y = e.clientY + pad;
      if (x + r.width > innerWidth - 8) x = e.clientX - r.width - pad;
      if (y + r.height > innerHeight - 8) y = e.clientY - r.height - pad;
      tip.style.left = x + "px"; tip.style.top = y + "px";
    });
    table.addEventListener("pointerleave", () => { tip.hidden = true; });
  }
})();
