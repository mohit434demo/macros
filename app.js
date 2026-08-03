/* Macros - phone-first nutrition tracker.
   All user data stays in localStorage on this device. */
(() => {
"use strict";

// ---------------------------------------------------------------- storage
const KEY = "nt.v1";
const DEFAULTS = {
  targets: { cal: 1875, pro: 140, fat: 52, carb: 212, fib: 35, goalWeight: 165 },
  profile: { age: 31, heightIn: 67, sex: "m", act: 1.375 },
  log: {},        // "YYYY-MM-DD" -> [{id,name,meal,qty,cal,p,c,f,src}]
  measures: {},   // "YYYY-MM-DD" -> {w: lb, waist: in}
  custom: [],     // [{id,n,cal,p,c,f,unit}]
};

let S = load();

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return structuredClone(DEFAULTS);
    const parsed = JSON.parse(raw);
    return {
      targets:  Object.assign({}, DEFAULTS.targets,  parsed.targets),
      profile:  Object.assign({}, DEFAULTS.profile,  parsed.profile),
      log:      parsed.log      || {},
      measures: parsed.measures || {},
      custom:   parsed.custom   || [],
    };
  } catch (e) {
    console.warn("load failed", e);
    return structuredClone(DEFAULTS);
  }
}
let saveTimer = null;
function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    try { localStorage.setItem(KEY, JSON.stringify(S)); }
    catch (e) { toast("Could not save - storage full?"); }
  }, 60);
}

// ---------------------------------------------------------------- helpers
const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const round = (n, d = 0) => { const m = 10 ** d; return Math.round(n * m) / m; };

function esc(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function todayKey() { return dayKey(new Date()); }
function dayKey(d) {
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") +
         "-" + String(d.getDate()).padStart(2, "0");
}
function parseKey(k) { const [y, m, d] = k.split("-").map(Number); return new Date(y, m - 1, d); }
function shiftKey(k, n) { const d = parseKey(k); d.setDate(d.getDate() + n); return dayKey(d); }
function prettyDate(k) {
  if (k === todayKey()) return "Today";
  if (k === shiftKey(todayKey(), -1)) return "Yesterday";
  return parseKey(k).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

let toastTimer = null;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 1900);
}

// ---------------------------------------------------------------- state
let curDate = todayKey();
let curView = "today";
let pendingMeal = "Lunch";
const MEALS = ["Breakfast", "Lunch", "Dinner", "Snack"];

function entries(k = curDate) { return S.log[k] || []; }
function totals(k = curDate) {
  return entries(k).reduce((t, e) => {
    t.cal += e.cal; t.p += e.p; t.c += e.c; t.f += e.f;
    return t;
  }, { cal: 0, p: 0, c: 0, f: 0 });
}

// ---------------------------------------------------------------- food index
function foodList() {
  const out = RECIPES.map(r => ({
    id: r.id, n: r.n, cal: r.cal, p: r.p, c: r.c, f: r.f,
    unit: "serving", sv: r.sv, ctp: r.ctp, tags: r.tags, src: "recipe", ref: r,
  }));
  for (const c of S.custom) {
    out.push({ id: c.id, n: c.n, cal: c.cal, p: c.p, c: c.c, f: c.f,
               unit: c.unit || "serving", ctp: c.p ? round(c.cal / c.p, 1) : null,
               tags: ["mine"], src: "custom" });
  }
  return out;
}
function findFood(id) { return foodList().find(f => f.id === id); }

function searchFoods(q, list) {
  const items = list || foodList();
  const s = q.trim().toLowerCase();
  if (!s) return items;
  const words = s.split(/\s+/);
  return items
    .map(f => {
      const n = f.n.toLowerCase();
      let score = 0;
      for (const w of words) {
        if (!n.includes(w)) return null;
        score += n.startsWith(w) ? 3 : 1;
      }
      return { f, score };
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score || a.f.n.localeCompare(b.f.n))
    .map(x => x.f);
}

// ---------------------------------------------------------------- TODAY view
function renderToday() {
  const t = totals();
  const g = S.targets;
  const left = g.cal - t.cal;

  $("#kcalLeft").textContent = Math.abs(round(left));
  $(".ring-lbl").textContent = left < 0 ? "over" : "left";
  $("#kcalEaten").textContent = round(t.cal);
  $("#kcalTarget").textContent = g.cal;
  $("#ctpToday").textContent = t.p > 0 ? round(t.cal / t.p, 1) : "-";

  const pct = clamp(g.cal ? t.cal / g.cal : 0, 0, 1);
  const C = 2 * Math.PI * 52;
  const ring = $("#ringFill");
  ring.style.strokeDasharray = C;
  ring.style.strokeDashoffset = C * (1 - pct);
  ring.classList.toggle("over", t.cal > g.cal);

  const rows = [
    ["Protein", t.p, g.pro, "g", "m-protein"],
    ["Carbs",   t.c, g.carb, "g", "m-carbs"],
    ["Fat",     t.f, g.fat, "g", "m-fat"],
  ];
  $("#macroBars").innerHTML = rows.map(([name, val, tgt, u, cls]) => {
    const p = tgt ? clamp(val / tgt, 0, 1) * 100 : 0;
    const over = val > tgt * 1.05;
    return `<div class="mrow">
      <span class="name">${name}</span>
      <span class="bar"><i class="${over ? "over" : cls}" style="width:${p}%"></i></span>
      <span class="val">${round(val)} / ${tgt}${u}</span>
    </div>`;
  }).join("");

  const byMeal = {};
  for (const m of MEALS) byMeal[m] = [];
  entries().forEach((e, i) => { (byMeal[e.meal] || byMeal.Snack).push({ e, i }); });

  $("#meals").innerHTML = MEALS.map(m => {
    const list = byMeal[m];
    const cals = list.reduce((s, x) => s + x.e.cal, 0);
    const body = list.map(({ e, i }) => `
      <div class="entry">
        <div class="e-main">
          <div class="e-name">${esc(e.name)}</div>
          <div class="e-sub">${e.qty === 1 ? "1 serving" : e.qty + " servings"} &middot; ${round(e.p)}p ${round(e.c)}c ${round(e.f)}f</div>
        </div>
        <span class="e-cal">${round(e.cal)}</span>
        <button class="del" data-del="${i}" aria-label="Remove">&times;</button>
      </div>`).join("");
    return `<div class="meal">
      <div class="meal-head"><strong>${m}</strong><em>${cals ? round(cals) + " cal" : ""}</em></div>
      ${body}
      <button class="add-line" data-addmeal="${m}">+ Add to ${m.toLowerCase()}</button>
    </div>`;
  }).join("");

  const note = [];
  if (t.cal > 0) {
    if (t.p < g.pro * 0.7 && t.cal > g.cal * 0.7) note.push("Protein is lagging behind calories today.");
    if (left < -200) note.push("You are meaningfully over target.");
    else if (left > 400 && new Date().getHours() >= 20) note.push("Big gap left. Under-eating is not a win; it usually shows up as a binge later.");
  }
  $("#dayNote").textContent = note.join(" ");
}

// ---------------------------------------------------------------- COOKBOOK
let cbTag = "all";
let cbSort = "name";
const TAGS = ["all", "chicken", "beef", "pasta", "rice", "burrito", "breakfast", "pizza", "soup", "mine"];
const SORTS = [["name", "A-Z"], ["ctp", "Best protein ratio"], ["cal", "Fewest calories"], ["p", "Most protein"]];

function renderCookbook() {
  $("#cbChips").innerHTML = TAGS.map(t =>
    `<button class="chip ${t === cbTag ? "on" : ""}" data-tag="${t}">${t === "all" ? "All" : t[0].toUpperCase() + t.slice(1)}</button>`).join("");
  $("#cbSort").innerHTML = SORTS.map(([k, l]) =>
    `<button class="chip ${k === cbSort ? "on" : ""}" data-sort="${k}">${l}</button>`).join("");

  let list = foodList();
  if (cbTag !== "all") list = list.filter(f => f.tags.includes(cbTag));
  list = searchFoods($("#cbSearch").value, list);

  if (cbSort === "ctp")      list = list.slice().sort((a, b) => (a.ctp ?? 99) - (b.ctp ?? 99));
  else if (cbSort === "cal") list = list.slice().sort((a, b) => a.cal - b.cal);
  else if (cbSort === "p")   list = list.slice().sort((a, b) => b.p - a.p);
  else                       list = list.slice().sort((a, b) => a.n.localeCompare(b.n));

  $("#cbList").innerHTML = list.length ? list.map(f => `
    <button class="row" data-food="${esc(f.id)}">
      <span class="r-main">
        <span class="r-name">${esc(f.n)}</span>
        <span class="r-sub">${f.cal} cal &middot; ${f.p}p ${f.c}c ${f.f}f${f.sv ? " &middot; makes " + f.sv : ""}</span>
      </span>
      <span class="badge ${f.ctp && f.ctp <= 11 ? "good" : ""}">${f.ctp ?? "-"}</span>
    </button>`).join("")
    : `<p class="empty">Nothing matches that.</p>`;
}

// ---------------------------------------------------------------- PROGRESS
function measureSeries() {
  return Object.keys(S.measures).sort().map(k => ({ k, ...S.measures[k] }));
}
function rollingAvg(pts, field, win = 7) {
  return pts.map((p, i) => {
    const from = Math.max(0, i - win + 1);
    const slice = pts.slice(from, i + 1).filter(x => typeof x[field] === "number");
    if (!slice.length) return { k: p.k, v: null };
    return { k: p.k, v: slice.reduce((s, x) => s + x[field], 0) / slice.length };
  });
}

function lineChart(pts, avg, unit, goal) {
  const vals = pts.map(p => p.v).filter(v => v != null);
  if (vals.length < 2) return `<p class="empty">Log at least two days to see a trend.</p>`;
  const W = 320, H = 130, PL = 34, PR = 8, PT = 10, PB = 18;
  const all = vals.concat(goal != null ? [goal] : []);
  let min = Math.min(...all), max = Math.max(...all);
  const pad = (max - min) * 0.15 || 1;
  min -= pad; max += pad;
  const x = i => PL + (i / Math.max(1, pts.length - 1)) * (W - PL - PR);
  const y = v => PT + (1 - (v - min) / (max - min)) * (H - PT - PB);

  const dots = pts.filter(p => p.v != null)
    .map(p => `<circle cx="${round(x(pts.indexOf(p)), 1)}" cy="${round(y(p.v), 1)}" r="2" fill="var(--cp-border-strong)"/>`).join("");
  const avgPts = avg.map((p, i) => p.v == null ? null : `${round(x(i), 1)},${round(y(p.v), 1)}`).filter(Boolean);
  const avgLine = avgPts.length > 1
    ? `<polyline points="${avgPts.join(" ")}" fill="none" stroke="var(--cp-accent)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>` : "";
  const goalLine = goal != null && goal > min && goal < max
    ? `<line x1="${PL}" y1="${round(y(goal), 1)}" x2="${W - PR}" y2="${round(y(goal), 1)}" stroke="var(--cp-accent)" stroke-width="1" stroke-dasharray="4 4" opacity="0.55"/>
       <text x="${W - PR}" y="${round(y(goal), 1) - 4}" font-size="8" text-anchor="end" fill="var(--cp-text-muted)">goal ${goal}</text>` : "";

  const ticks = [max - pad * 0.6, (min + max) / 2, min + pad * 0.6].map(v =>
    `<text x="${PL - 5}" y="${round(y(v), 1) + 3}" font-size="8" text-anchor="end" fill="var(--cp-text-muted)">${round(v, 1)}</text>`).join("");
  const first = pts[0].k.slice(5), last = pts[pts.length - 1].k.slice(5);

  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="trend chart">
    ${ticks}${goalLine}${dots}${avgLine}
    <text x="${PL}" y="${H - 4}" font-size="8" fill="var(--cp-text-muted)">${first}</text>
    <text x="${W - PR}" y="${H - 4}" font-size="8" text-anchor="end" fill="var(--cp-text-muted)">${last}</text>
  </svg>`;
}

function renderProgress() {
  const m = S.measures[curDate] || {};
  $("#inWeight").value = m.w ?? "";
  $("#inWaist").value = m.waist ?? "";

  const pts = measureSeries();
  const wPts = pts.map(p => ({ k: p.k, v: p.w ?? null }));
  const wAvg = rollingAvg(pts.map(p => ({ k: p.k, w: p.w })), "w");
  $("#weightChart").innerHTML = lineChart(wPts, wAvg, "lb", S.targets.goalWeight);

  const waistPts = pts.map(p => ({ k: p.k, v: p.waist ?? null }));
  const waistAvg = rollingAvg(pts.map(p => ({ k: p.k, waist: p.waist })), "waist");
  $("#waistChart").innerHTML = lineChart(waistPts, waistAvg, "in", null);

  const weights = pts.filter(p => typeof p.w === "number");
  const waists  = pts.filter(p => typeof p.waist === "number");
  const trendNow = wAvg.filter(a => a.v != null).slice(-1)[0]?.v ?? null;
  const start = weights[0]?.w ?? null;
  const toGo = trendNow != null ? trendNow - S.targets.goalWeight : null;

  const cells = [];
  cells.push(["Trend weight", trendNow != null ? round(trendNow, 1) + " lb" : "-"]);
  cells.push(["Change", start != null && trendNow != null ? (trendNow - start >= 0 ? "+" : "") + round(trendNow - start, 1) + " lb" : "-"]);
  cells.push(["To goal", toGo != null ? round(toGo, 1) + " lb" : "-"]);
  cells.push(["Days logged", String(weights.length)]);
  if (waists.length) {
    const wl = waists[waists.length - 1].waist;
    cells.push(["Waist now", round(wl, 1) + " in"]);
    cells.push(["Waist change", (wl - waists[0].waist >= 0 ? "+" : "") + round(wl - waists[0].waist, 1) + " in"]);
  }
  $("#progStats").innerHTML = cells.map(([l, v]) => `<div><b>${v}</b><small>${l}</small></div>`).join("");

  $("#tdeeBox").innerHTML = tdeeReport(pts, wAvg);
}

/* Back-calculate maintenance from real intake vs real trend-weight change.
   3500 kcal per pound of bodyweight is the standard working figure. */
function tdeeReport(pts, wAvg) {
  const avail = wAvg.filter(a => a.v != null);
  if (avail.length < 10) {
    return `<p class="hint">Needs about 14 days of weight and food logs. So far: ${avail.length}.</p>`;
  }
  const end = avail[avail.length - 1];
  const startIdx = Math.max(0, avail.length - 15);
  const start = avail[startIdx];
  const days = Math.round((parseKey(end.k) - parseKey(start.k)) / 86400000);
  if (days < 7) return `<p class="hint">Needs a longer window of daily weigh-ins.</p>`;

  let kcal = 0, n = 0;
  for (let i = 0; i <= days; i++) {
    const k = shiftKey(start.k, i);
    const e = S.log[k];
    if (e && e.length) { kcal += e.reduce((s, x) => s + x.cal, 0); n++; }
  }
  if (n < days * 0.6) {
    return `<p class="hint">Only ${n} of the last ${days} days have food logged. Log more consistently for this to work.</p>`;
  }
  const avgIntake = kcal / n;
  const lbChange = end.v - start.v;
  const tdee = avgIntake - (lbChange * 3500) / days;
  const rate = (lbChange / days) * 7;
  const deficit = tdee - S.targets.cal;

  let advice;
  if (Math.abs(rate) < 0.2) {
    advice = "Weight is flat. If your waist is also flat, drop calories by about 150. If waist is still shrinking, hold: you are recomping.";
  } else if (rate < -1.5) {
    advice = "Losing faster than 1.5 lb per week. That pace costs muscle. Add roughly 150 to 200 calories.";
  } else if (rate < 0) {
    advice = "On pace. Keep going and change nothing.";
  } else {
    advice = "Trending up. Tighten portion accuracy before cutting calories further, since logging drift is the usual culprit.";
  }

  const weeks = deficit > 0 && end.v > S.targets.goalWeight
    ? round((end.v - S.targets.goalWeight) / Math.max(0.1, Math.abs(rate)), 0) : null;

  return `<div class="stat-grid">
      <div><b>${round(tdee)}</b><small>estimated maintenance</small></div>
      <div><b>${round(avgIntake)}</b><small>avg intake, ${n} days</small></div>
      <div><b>${rate >= 0 ? "+" : ""}${round(rate, 2)}</b><small>lb per week</small></div>
      <div><b>${round(deficit)}</b><small>actual daily deficit</small></div>
    </div>
    <div class="callout">${advice}${weeks && weeks < 200 ? ` At this rate you reach ${S.targets.goalWeight} lb in about ${weeks} weeks.` : ""}</div>`;
}

// ---------------------------------------------------------------- SETTINGS
function renderMore() {
  const t = S.targets, p = S.profile;
  $("#tCal").value = t.cal; $("#tPro").value = t.pro;
  $("#tFat").value = t.fat; $("#tCarb").value = t.carb;
  $("#tFib").value = t.fib; $("#tGoal").value = t.goalWeight;
  $("#pAge").value = p.age; $("#pHeight").value = p.heightIn;
  $("#pAct").value = String(p.act);

  $("#customList").innerHTML = S.custom.length ? S.custom.map(c => `
    <div class="row">
      <span class="r-main">
        <span class="r-name">${esc(c.n)}</span>
        <span class="r-sub">${c.cal} cal &middot; ${c.p}p ${c.c}c ${c.f}f per ${esc(c.unit || "serving")}</span>
      </span>
      <button class="del" data-delcustom="${esc(c.id)}" aria-label="Remove">&times;</button>
    </div>`).join("") : `<p class="hint">No custom foods yet.</p>`;
}

function recalcTargets() {
  const p = S.profile;
  const pts = measureSeries().filter(x => typeof x.w === "number");
  const wLb = pts.length ? pts[pts.length - 1].w : 185;
  const kg = wLb * 0.4536, cm = p.heightIn * 2.54;
  const bmr = 10 * kg + 6.25 * cm - 5 * p.age + 5;      // Mifflin-St Jeor, male
  const tdee = bmr * p.act;
  const cal = Math.round((tdee - 500) / 25) * 25;
  const pro = Math.round((kg * 1.9) / 5) * 5;            // ~1.9 g/kg for a lifter cutting
  const fat = Math.round((cal * 0.25 / 9) / 2) * 2;
  const carb = Math.round((cal - pro * 4 - fat * 9) / 4);
  Object.assign(S.targets, { cal, pro, fat, carb });
  save(); renderMore(); renderToday();
  $("#calcNote").textContent =
    `BMR ${Math.round(bmr)}, maintenance about ${Math.round(tdee)} at your activity level. ` +
    `Target set to ${cal} for roughly 1 lb per week, protein ${pro}g (1.9 g/kg).`;
  toast("Targets updated");
}

// ---------------------------------------------------------------- sheets
function openSheet(id) {
  $("#scrim").hidden = false;
  $("#" + id).hidden = false;
  document.body.style.overflow = "hidden";
}
function closeSheets() {
  $$(".sheet").forEach(s => { s.hidden = true; });
  $("#scrim").hidden = true;
  document.body.style.overflow = "";
}

function openAdd(meal) {
  pendingMeal = meal || guessMeal();
  $("#mealSeg").innerHTML = MEALS.map(m =>
    `<button class="${m === pendingMeal ? "on" : ""}" data-meal="${m}">${m}</button>`).join("");
  $("#addSearch").value = "";
  renderAddResults();
  openSheet("sheetAdd");
}
function guessMeal() {
  const h = new Date().getHours();
  if (h < 10.5) return "Breakfast";
  if (h < 15) return "Lunch";
  if (h < 21) return "Dinner";
  return "Snack";
}
function renderAddResults() {
  const q = $("#addSearch").value;
  const list = searchFoods(q).slice(0, 60);
  $("#addResults").innerHTML = list.length ? list.map(f => `
    <button class="row" data-pick="${esc(f.id)}">
      <span class="r-main">
        <span class="r-name">${esc(f.n)}</span>
        <span class="r-sub">${f.cal} cal &middot; ${f.p}p ${f.c}c ${f.f}f</span>
      </span>
      <span class="badge ${f.ctp && f.ctp <= 11 ? "good" : ""}">${f.ctp ?? "-"}</span>
    </button>`).join("") : `<p class="empty">No match. Add it under More &rsaquo; My foods.</p>`;
}

let portionFood = null, portionQty = 1;
function openPortion(id) {
  portionFood = findFood(id);
  if (!portionFood) return;
  portionQty = 1;
  renderPortion();
  openSheet("sheetPortion");
}
function renderPortion() {
  const f = portionFood, q = portionQty;
  const mk = (v, l) => `<div><b>${round(f[v] * q, v === "cal" ? 0 : 1)}</b><small>${l}</small></div>`;
  $("#portionBody").innerHTML = `
    <h3>${esc(f.n)}</h3>
    <p class="hint">Per ${esc(f.unit)}: ${f.cal} cal, ${f.p}p ${f.c}c ${f.f}f${f.sv ? `. Recipe makes ${f.sv}.` : ""}</p>
    <div class="qty-row">
      <button data-q="-">&minus;</button>
      <input id="qtyIn" type="number" inputmode="decimal" step="0.25" min="0.25" value="${q}">
      <button data-q="+">+</button>
    </div>
    <div class="chips" style="justify-content:center">
      ${[0.5, 1, 1.5, 2].map(v => `<button class="chip ${v === q ? "on" : ""}" data-setq="${v}">${v}x</button>`).join("")}
    </div>
    <div class="preview">${mk("cal", "cal")}${mk("p", "protein")}${mk("c", "carbs")}${mk("f", "fat")}</div>
    <button class="btn primary full" id="confirmAdd">Add to ${pendingMeal.toLowerCase()}</button>
    ${f.src === "recipe" ? `<button class="btn full" id="viewRecipe">View recipe</button>` : ""}`;
}
function commitAdd() {
  const f = portionFood, q = Number(portionQty) || 1;
  const list = S.log[curDate] || (S.log[curDate] = []);
  list.push({
    fid: f.id, name: f.n, meal: pendingMeal, qty: round(q, 2),
    cal: round(f.cal * q), p: round(f.p * q, 1), c: round(f.c * q, 1), f: round(f.f * q, 1),
    src: f.src,
  });
  save(); closeSheets(); go("today"); renderToday();
  toast(`Added to ${pendingMeal.toLowerCase()}`);
}

function openRecipe(id) {
  const r = RECIPES.find(x => x.id === id);
  if (!r) return;
  $("#recipeBody").innerHTML = `
    <h3>${esc(r.n)}</h3>
    <p class="hint">${r.cal} cal &middot; ${r.p}g protein &middot; ${r.c}g carbs &middot; ${r.f}g fat per serving${r.sv ? `. Makes ${r.sv}.` : ""}</p>
    <div class="preview">
      <div><b>${r.ctp ?? "-"}</b><small>cal per g protein</small></div>
      <div><b>${r.sv ?? "-"}</b><small>servings</small></div>
      <div><b>${round(r.p * 4 / r.cal * 100)}%</b><small>from protein</small></div>
      <div><b>${r.ed ? "#" + r.ed : "-"}</b><small>edition</small></div>
    </div>
    <button class="btn primary full" data-logthis="${esc(r.id)}">Log this</button>
    ${r.ing.length ? `<h3>Ingredients</h3><ul class="ing-list">${r.ing.map(i => `<li>${esc(i)}</li>`).join("")}</ul>` : ""}
    ${r.st.length ? `<h3>Instructions</h3><ol class="step-list">${r.st.map(s => `<li>${esc(s)}</li>`).join("")}</ol>` : ""}`;
  openSheet("sheetRecipe");
}

function openCustom() {
  $("#customBody").innerHTML = `
    <label class="block">Name <input id="cName" placeholder="Whey shake"></label>
    <label class="block">Unit <input id="cUnit" placeholder="scoop, bowl, serving" value="serving"></label>
    <div class="field-row">
      <label>Calories <input id="cCal" type="number" inputmode="numeric"></label>
      <label>Protein (g) <input id="cP" type="number" inputmode="decimal"></label>
    </div>
    <div class="field-row">
      <label>Carbs (g) <input id="cC" type="number" inputmode="decimal"></label>
      <label>Fat (g) <input id="cF" type="number" inputmode="decimal"></label>
    </div>
    <button class="btn primary full" id="saveCustom">Save food</button>`;
  openSheet("sheetCustom");
}

// ---------------------------------------------------------------- nav
function go(view) {
  curView = view;
  $$(".view").forEach(v => { v.hidden = v.id !== "view-" + view; });
  $$(".tab").forEach(t => t.classList.toggle("active", t.dataset.view === view));
  $("#viewTitle").textContent =
    { today: "Today", cookbook: "Cookbook", progress: "Progress", more: "More" }[view];
  const dateNav = view === "today" || view === "progress";
  $("#dateBack").hidden = $("#dateFwd").hidden = $("#dateLabel").hidden = !dateNav;
  $("#fab").hidden = view !== "today" && view !== "cookbook";
  if (view === "today") renderToday();
  if (view === "cookbook") renderCookbook();
  if (view === "progress") renderProgress();
  if (view === "more") renderMore();
  window.scrollTo(0, 0);
}
function setDate(k) {
  if (k > todayKey()) return;
  curDate = k;
  $("#dateLabel").textContent = prettyDate(k);
  if (curView === "today") renderToday();
  if (curView === "progress") renderProgress();
}

// ---------------------------------------------------------------- events
document.addEventListener("click", ev => {
  const el = ev.target.closest("[data-view],[data-tag],[data-sort],[data-food],[data-pick],[data-meal],[data-setq],[data-q],[data-del],[data-addmeal],[data-delcustom],[data-logthis],[data-close]");
  if (!el) return;
  const d = el.dataset;

  if (d.view) return go(d.view);
  if (d.close !== undefined) return closeSheets();
  if (d.tag) { cbTag = d.tag; return renderCookbook(); }
  if (d.sort) { cbSort = d.sort; return renderCookbook(); }
  if (d.food) { const f = findFood(d.food); return f && f.src === "recipe" ? openRecipe(d.food) : openPortion(d.food); }
  if (d.pick) return openPortion(d.pick);
  if (d.logthis) { closeSheets(); return openPortion(d.logthis); }
  if (d.meal) { pendingMeal = d.meal; $$("#mealSeg button").forEach(b => b.classList.toggle("on", b.dataset.meal === d.meal)); return; }
  if (d.setq) { portionQty = Number(d.setq); return renderPortion(); }
  if (d.q) { portionQty = Math.max(0.25, round(portionQty + (d.q === "+" ? 0.25 : -0.25), 2)); return renderPortion(); }
  if (d.addmeal) return openAdd(d.addmeal);
  if (d.del !== undefined) {
    S.log[curDate].splice(Number(d.del), 1);
    if (!S.log[curDate].length) delete S.log[curDate];
    save(); return renderToday();
  }
  if (d.delcustom) {
    S.custom = S.custom.filter(c => c.id !== d.delcustom);
    save(); return renderMore();
  }
});

$("#scrim").addEventListener("click", closeSheets);
$("#fab").addEventListener("click", () => curView === "cookbook" ? openAdd() : openAdd());
$("#cbSearch").addEventListener("input", renderCookbook);
$("#addSearch").addEventListener("input", renderAddResults);

document.addEventListener("input", ev => {
  if (ev.target.id === "qtyIn") {
    portionQty = Math.max(0.25, Number(ev.target.value) || 1);
    const f = portionFood;
    const cells = $$("#portionBody .preview b");
    if (cells.length === 4) {
      cells[0].textContent = round(f.cal * portionQty);
      cells[1].textContent = round(f.p * portionQty, 1);
      cells[2].textContent = round(f.c * portionQty, 1);
      cells[3].textContent = round(f.f * portionQty, 1);
    }
  }
});

document.addEventListener("click", ev => {
  const id = ev.target.id;
  if (id === "confirmAdd") return commitAdd();
  if (id === "viewRecipe") { closeSheets(); return openRecipe(portionFood.id); }
  if (id === "dateBack") return setDate(shiftKey(curDate, -1));
  if (id === "dateFwd")  return setDate(shiftKey(curDate, 1));
  if (id === "dateLabel") return setDate(todayKey());
  if (id === "themeBtn") {
    const cur = document.documentElement.getAttribute("data-theme");
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("nt.theme", next); } catch (e) {}
    if (curView === "progress") renderProgress();
    return;
  }
  if (id === "saveMeasure") {
    const w = parseFloat($("#inWeight").value), wa = parseFloat($("#inWaist").value);
    if (!w && !wa) return toast("Enter a weight or waist first");
    const m = S.measures[curDate] || (S.measures[curDate] = {});
    if (w) m.w = w;
    if (wa) m.waist = wa;
    save(); renderProgress(); toast("Saved");
    return;
  }
  if (id === "saveTargets") {
    S.targets = {
      cal: +$("#tCal").value || 1875, pro: +$("#tPro").value || 140,
      fat: +$("#tFat").value || 52, carb: +$("#tCarb").value || 212,
      fib: +$("#tFib").value || 35, goalWeight: +$("#tGoal").value || 165,
    };
    save(); renderToday(); toast("Targets saved");
    return;
  }
  if (id === "recalc") {
    S.profile = {
      age: +$("#pAge").value || 31, heightIn: +$("#pHeight").value || 67,
      sex: "m", act: +$("#pAct").value || 1.375,
    };
    save(); return recalcTargets();
  }
  if (id === "addCustom") return openCustom();
  if (id === "saveCustom") {
    const n = $("#cName").value.trim();
    if (!n) return toast("Name it first");
    S.custom.push({
      id: "c" + Date.now().toString(36), n,
      unit: $("#cUnit").value.trim() || "serving",
      cal: +$("#cCal").value || 0, p: +$("#cP").value || 0,
      c: +$("#cC").value || 0, f: +$("#cF").value || 0,
    });
    save(); closeSheets(); renderMore(); toast("Food saved");
    return;
  }
  if (id === "exportBtn") {
    const blob = new Blob([JSON.stringify(S, null, 1)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `macros-backup-${todayKey()}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    return;
  }
  if (id === "importBtn") return $("#importFile").click();
  if (id === "resetBtn") {
    if (confirm("Erase all logged food, weights and settings on this device?")) {
      S = structuredClone(DEFAULTS); save(); go("today"); toast("Erased");
    }
    return;
  }
});

$("#importFile").addEventListener("change", ev => {
  const file = ev.target.files[0];
  if (!file) return;
  const fr = new FileReader();
  fr.onload = () => {
    try {
      const d = JSON.parse(fr.result);
      S = {
        targets: Object.assign({}, DEFAULTS.targets, d.targets),
        profile: Object.assign({}, DEFAULTS.profile, d.profile),
        log: d.log || {}, measures: d.measures || {}, custom: d.custom || [],
      };
      save(); go("today"); toast("Data imported");
    } catch (e) { toast("That file could not be read"); }
  };
  fr.readAsText(file);
  ev.target.value = "";
});

// swipe between days on the Today view
let tx = 0, ty = 0;
document.addEventListener("touchstart", e => {
  tx = e.changedTouches[0].clientX; ty = e.changedTouches[0].clientY;
}, { passive: true });
document.addEventListener("touchend", e => {
  if (curView !== "today") return;
  if ($$(".sheet").some(s => !s.hidden)) return;
  const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
  if (Math.abs(dx) > 70 && Math.abs(dy) < 50) setDate(shiftKey(curDate, dx > 0 ? -1 : 1));
}, { passive: true });

// ---------------------------------------------------------------- boot
$("#cbSearch").setAttribute("placeholder", `Search ${RECIPES.length} recipes...`);
setDate(todayKey());
go("today");

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}
})();
