/* Macros - phone-first nutrition tracker.
   All user data stays in localStorage on this device. */
(() => {
"use strict";

// ---------------------------------------------------------------- storage
const KEY = "nt.v1";
const DEFAULTS = {
  targets: { cal: 1875, pro: 140, fat: 52, carb: 212, fib: 35, goalWeight: 165, water: 100 },
  profile: { age: 31, heightIn: 67, sex: "m", act: 1.375 },
  log: {},        // "YYYY-MM-DD" -> [{id,name,meal,qty,cal,p,c,f,src}]
  measures: {},   // "YYYY-MM-DD" -> {w: lb, waist: in}
  water: {},      // "YYYY-MM-DD" -> ounces
  custom: [],     // [{id,n,cal,p,c,f,unit,parts?}]
  usage: {},      // foodId -> {n: times logged, last: "YYYY-MM-DD"}
  marks: {},      // foodId -> "rotation" | "want" | "skip"
  edits: {},      // bundled foodId -> {n?,unit?,cal,p,c,f} user corrections
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
      water:    parsed.water    || {},
      custom:   parsed.custom   || [],
      usage:    parsed.usage    || {},
      marks:    parsed.marks    || {},
      edits:    parsed.edits    || {},
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
/* A custom entry may be a simple food or a "meal": a named combination of other
   foods with quantities. Meal macros are derived from their parts every time,
   so correcting a component fixes every meal that uses it. Parts may only
   reference simple foods, which keeps this non-recursive. */
function simpleFoods() {
  const out = RECIPES.map(r => ({
    id: r.id, n: r.n, cal: r.cal, p: r.p, c: r.c, f: r.f,
    unit: "serving", sv: r.sv, ctp: r.ctp, tags: r.tags, src: "recipe", ref: r,
  }));
  for (const b of (typeof PANTRY !== "undefined" ? PANTRY : [])) {
    if (b.parts && b.parts.length) continue;
    out.push({ id: b.id, n: b.n, cal: b.cal, p: b.p, c: b.c, f: b.f,
               unit: b.unit || "serving", tags: b.tags || ["pantry"], src: "pantry",
               per100: !!b.per100, freeCal: !!b.freeCal });
  }
  for (const c of S.custom) {
    if (c.parts && c.parts.length) continue;
    out.push({ id: c.id, n: c.n, cal: c.cal, p: c.p, c: c.c, f: c.f,
               unit: c.unit || "serving", tags: ["mine"], src: "custom",
               per100: !!c.per100, freeCal: !!c.freeCal });
  }
  // user corrections win over bundled values
  return out.map(f => {
    const e = S.edits[f.id];
    if (!e) return withCtp(f);
    return withCtp({ ...f, ...e, edited: true });
  });
}
function withCtp(f) {
  f.ctp = f.p ? round(f.cal / f.p, 1) : null;
  return f;
}

function mealTotals(parts, base) {
  const idx = base || new Map(simpleFoods().map(f => [f.id, f]));
  const t = { cal: 0, p: 0, c: 0, f: 0, missing: 0 };
  for (const p of parts) {
    const f = idx.get(p.id);
    if (!f) { t.missing++; continue; }
    t.cal += f.cal * p.qty; t.p += f.p * p.qty;
    t.c += f.c * p.qty;     t.f += f.f * p.qty;
  }
  t.cal = round(t.cal); t.p = round(t.p, 1); t.c = round(t.c, 1); t.f = round(t.f, 1);
  return t;
}

function foodList() {
  const simple = simpleFoods();
  const idx = new Map(simple.map(f => [f.id, f]));
  const out = simple.slice();
  const combos = [
    ...(typeof PANTRY !== "undefined" ? PANTRY : []).filter(b => b.parts && b.parts.length)
      .map(b => ({ ...b, src: "pantry" })),
    ...S.custom.filter(c => c.parts && c.parts.length).map(c => ({ ...c, src: "custom" })),
  ];
  for (const c of combos) {
    const t = mealTotals(c.parts, idx);
    out.push({ id: c.id, n: c.n, cal: t.cal, p: t.p, c: t.c, f: t.f,
               unit: c.unit || "meal", ctp: t.p ? round(t.cal / t.p, 1) : null,
               tags: c.tags || ["mine", "meal"], src: c.src, parts: c.parts });
  }
  return out;
}
function findFood(id) { return foodList().find(f => f.id === id); }

/* The shortlist is earned: anything logged once joins it automatically.
   Explicit marks let you pin something you have not eaten yet, or hide
   something you tried and did not like. */
/* Only the foods explicitly set up for Mohit start in the shortlist. The wider
   staple library stays one search away so "My foods" does not become a wall. */
const STARTER = new Set([
  "s-rice-white", "s-chicken-thigh", "s-sauce-addon", "s-olive-oil", "s-bouillon",
  "p-dkb-white-bun", "p-deli-turkey", "p-deli-ham", "p-ayoh-dill",
  "p-kraft-single", "p-popcorners-kettle", "p-bero-shandy",
  "p-sandwich-meal",
]);

function isPantry(id) {
  return typeof PANTRY !== "undefined" && PANTRY.some(b => b.id === id);
}
function inRotation(id) {
  if (S.marks[id] === "skip") return false;
  if (S.marks[id] === "rotation") return true;
  if ((S.usage[id]?.n || 0) > 0) return true;
  return STARTER.has(id);   // your everyday items start in the list
}
function rotationList() {
  return foodList()
    .filter(f => inRotation(f.id))
    .sort((a, b) => {
      const ua = S.usage[a.id] || { n: 0, last: "" };
      const ub = S.usage[b.id] || { n: 0, last: "" };
      // saved meals first, then most recently eaten, then most frequent
      const ma = a.parts ? 1 : 0, mb = b.parts ? 1 : 0;
      return mb - ma || (ub.last || "").localeCompare(ua.last || "")
             || ub.n - ua.n || a.n.localeCompare(b.n);
    });
}
function noteUsage(id, qty) {
  const u = S.usage[id] || (S.usage[id] = { n: 0, last: "" });
  u.n += 1;
  u.last = curDate;
  if (qty != null) u.q = qty;   // remember the portion for next time
  if (S.marks[id] === "want" || S.marks[id] === "skip") delete S.marks[id];
}

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

  renderWater();

  const byMeal = {};
  for (const m of MEALS) byMeal[m] = [];
  entries().forEach((e, i) => { (byMeal[e.meal] || byMeal.Snack).push({ e, i }); });

  const quick = rotationList().slice(0, 6);
  $("#quickAdd").innerHTML = quick.length ? `
    <div class="meal-head" style="padding-bottom:4px"><strong>Quick add</strong></div>
    <div class="chips">${quick.map(f =>
      `<button class="chip" data-again="${esc(f.id)}">${esc(f.n.length > 26 ? f.n.slice(0, 25) + "\u2026" : f.n)}</button>`).join("")}</div>` : "";

  $("#meals").innerHTML = MEALS.map(m => {
    const list = byMeal[m];
    const cals = list.reduce((s, x) => s + x.e.cal, 0);
    const body = list.map(({ e, i }) => `
      <div class="entry">
        <div class="e-main">
          <div class="e-name">${esc(e.name)}</div>
          <div class="e-sub">${esc(e.disp || (e.qty === 1 ? "1 serving" : e.qty + " servings"))} &middot; ${round(e.p)}p ${round(e.c)}c ${round(e.f)}f</div>
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

function renderWater() {
  const oz = S.water[curDate] || 0;
  const goal = S.targets.water || 100;
  $("#waterOz").textContent = oz;
  $("#waterGoal").textContent = goal;
  const pct = goal ? clamp(oz / goal, 0, 1) * 100 : 0;
  const bar = $("#waterBar");
  bar.style.width = pct + "%";
  bar.classList.toggle("done", oz >= goal);
}

function addWater(delta) {
  const oz = Math.max(0, (S.water[curDate] || 0) + delta);
  if (oz) S.water[curDate] = oz;
  else delete S.water[curDate];
  save();
  renderWater();
}

// ---------------------------------------------------------------- COOKBOOK
let cbTag = "all";
let cbSort = "name";
const TAGS = ["all", "rotation", "untried", "staple", "addon", "pantry", "meal",
              "joe", "stealth", "korean", "highprotein", "quick", "mealprep", "banchan",
              "chicken", "beef", "seafood", "pasta", "rice", "burrito", "breakfast", "pizza", "soup", "mine"];
const TAG_LABEL = { all: "All", rotation: "My rotation", untried: "Not tried yet",
                    mine: "My foods", pantry: "Everyday", meal: "Saved meals",
                    staple: "Staples", addon: "Add-ons",
                    joe: "Joe x Fitness", stealth: "Stealth Health",
                    highprotein: "High protein", quick: "30-minute",
                    mealprep: "Meal prep", banchan: "Banchan" };
const SORTS = [["name", "A-Z"], ["ctp", "Best protein ratio"], ["cal", "Fewest calories"], ["p", "Most protein"]];

function statusOf(id) {
  if (S.marks[id] === "skip") return "skip";
  if ((S.usage[id]?.n || 0) > 0) return "eaten";
  if (S.marks[id] === "rotation" || STARTER.has(id)) return "rotation";
  if (S.marks[id] === "want") return "want";
  return "new";
}
const STATUS_PILL = {
  eaten:    `<span class="pill eaten">In rotation</span>`,
  rotation: `<span class="pill eaten">In rotation</span>`,
  want:     `<span class="pill want">Want to try</span>`,
  skip:     `<span class="pill skip">Skipped</span>`,
  new:      "",
};

function renderCookbook() {
  $("#cbChips").innerHTML = TAGS.map(t =>
    `<button class="chip ${t === cbTag ? "on" : ""}" data-tag="${t}">${TAG_LABEL[t] || t[0].toUpperCase() + t.slice(1)}</button>`).join("");
  $("#cbSort").innerHTML = SORTS.map(([k, l]) =>
    `<button class="chip ${k === cbSort ? "on" : ""}" data-sort="${k}">${l}</button>`).join("");

  let list = foodList();
  if (cbTag === "rotation")      list = list.filter(f => inRotation(f.id));
  else if (cbTag === "untried")  list = list.filter(f => statusOf(f.id) === "new");
  else if (cbTag !== "all")      list = list.filter(f => f.tags.includes(cbTag));
  list = searchFoods($("#cbSearch").value, list);

  if (cbSort === "ctp")      list = list.slice().sort((a, b) => (a.ctp ?? 99) - (b.ctp ?? 99));
  else if (cbSort === "cal") list = list.slice().sort((a, b) => a.cal - b.cal);
  else if (cbSort === "p")   list = list.slice().sort((a, b) => b.p - a.p);
  else                       list = list.slice().sort((a, b) => a.n.localeCompare(b.n));

  $("#cbCount").textContent = `${list.length} of ${foodList().length}`;

  $("#cbList").innerHTML = list.length ? list.map(f => {
    const st = statusOf(f.id);
    const times = S.usage[f.id]?.n || 0;
    const unit = f.src === "recipe" ? "" : (f.per100 ? " / 100g" : ` / ${esc(f.unit)}`);
    return `<button class="row" data-food="${esc(f.id)}">
      <span class="r-main">
        <span class="r-name">${esc(f.n)}</span>
        <span class="r-sub">${f.cal} cal &middot; ${f.p}p ${f.c}c ${f.f}f${unit}${times ? ` &middot; logged ${times}x` : ""}</span>
        ${STATUS_PILL[st]}${f.parts ? `<span class="pill want">Meal</span>` : ""}${
          f.ref?.book === "Joe x Fitness" ? `<span class="pill book">Joe x Fitness</span>` : ""}
      </span>
      <span class="r-icons">${f.ref?.vid ? `<span class="mini" title="Has video">&#9654;</span>` : ""}</span>
      <span class="badge ${f.ctp && f.ctp <= 11 ? "good" : ""}">${f.ctp ?? "-"}</span>
    </button>`;
  }).join("") : `<p class="empty">Nothing matches that.</p>`;
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
  $("#tWater").value = t.water ?? 100;
  $("#pAge").value = p.age; $("#pHeight").value = p.heightIn;
  $("#pAct").value = String(p.act);

  $("#customList").innerHTML = S.custom.length ? S.custom.map(c => {
    const f = foodList().find(x => x.id === c.id) || c;
    const isMeal = c.parts && c.parts.length;
    return `<button class="row" data-editcustom="${esc(c.id)}">
      <span class="r-main">
        <span class="r-name">${esc(c.n)}</span>
        <span class="r-sub">${f.cal} cal &middot; ${f.p}p ${f.c}c ${f.f}f per ${esc(c.unit || "serving")}${
          isMeal ? ` &middot; ${c.parts.length} items` : ""}</span>
      </span>
      ${isMeal ? `<span class="pill eaten">Meal</span>` : ""}
    </button>`;
  }).join("") : `<p class="hint">No custom foods yet.</p>`;
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
  // backing out of the component picker returns to the meal being built
  if (partPicker) {
    partPicker = false;
    $$(".sheet").forEach(s => { s.hidden = true; });
    renderCustom();
    openSheet("sheetCustom");
    return;
  }
  $$(".sheet").forEach(s => { s.hidden = true; });
  $("#scrim").hidden = true;
  document.body.style.overflow = "";
  editingCustom = null;
}

let addScope = "mine";   // "mine" = earned shortlist, "all" = full library

function openAdd(meal) {
  pendingMeal = meal || guessMeal();
  addScope = rotationList().length ? "mine" : "all";
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

function foodRow(f, extra = "") {
  const times = S.usage[f.id]?.n || 0;
  const per = f.per100 ? " / 100g" : (f.src === "recipe" ? "" : ` / ${esc(f.unit)}`);
  const sub = `${f.cal} cal &middot; ${f.p}p ${f.c}c ${f.f}f${per}` +
              (times ? ` &middot; logged ${times}x` : "");
  return `<button class="row" data-pick="${esc(f.id)}">
      <span class="r-main">
        <span class="r-name">${esc(f.n)}</span>
        <span class="r-sub">${sub}</span>
      </span>
      ${extra}
      <span class="badge ${f.ctp && f.ctp <= 11 ? "good" : ""}">${f.ctp ?? "-"}</span>
    </button>`;
}

function renderAddResults() {
  const q = $("#addSearch").value.trim();
  const rot = rotationList();

  $("#addScope").innerHTML = `
    <button class="chip ${addScope === "mine" ? "on" : ""}" data-scope="mine">My foods (${rot.length})</button>
    <button class="chip ${addScope === "all" ? "on" : ""}" data-scope="all">Everything (${foodList().length})</button>`;

  // searching always falls back to the full library so nothing is unreachable
  const scope = (addScope === "all" || q) ? foodList() : rot;
  const list = searchFoods(q, scope).slice(0, 60);
  $("#addSearch").placeholder = addScope === "mine" && !q
    ? "Search everything..." : "Search recipes and foods...";

  if (!list.length) {
    $("#addResults").innerHTML = `<p class="empty">No match.<br>Add it under More &rsaquo; My foods.</p>`;
    return;
  }
  let html = "";
  if (addScope === "mine" && !q) {
    html += `<p class="hint legend-hint">Your usual foods, most recent first. Anything you log once lands here automatically.</p>`;
  }
  html += list.map(f => foodRow(f)).join("");
  if (addScope === "mine" && !q) {
    html += `<button class="add-line" data-scope="all" style="margin-top:8px">Browse everything</button>`;
  }
  $("#addResults").innerHTML = html;
}

let portionFood = null, portionQty = 1;

/* Gram staples and free-calorie add-ons are entered in their natural unit
   (grams, calories) rather than as a serving multiplier. Internally everything
   is still a multiplier of the base row, so the log format never changes. */
function inputMode(f) {
  if (f.per100) return { key: "g", label: "grams", step: 10, per: 100,
                         chips: [100, 150, 200, 250, 300] };
  if (f.freeCal) return { key: "cal", label: "calories", step: 10, per: f.cal || 10,
                          chips: [40, 80, 120, 200] };
  return null;
}
function qtyToInput(f, q) {
  const m = inputMode(f);
  return m ? round(q * m.per, m.key === "g" ? 0 : 0) : q;
}
function inputToQty(f, v) {
  const m = inputMode(f);
  return m ? v / m.per : v;
}

function openPortion(id) {
  portionFood = findFood(id);
  if (!portionFood) return;
  const m = inputMode(portionFood);
  // Portions vary day to day, so start from what you used last time for this
  // food rather than a fixed default.
  const last = S.usage[id]?.q;
  if (last) portionQty = last;
  else portionQty = m ? (m.key === "g" ? 1.5 : 8) : 1;   // 150 g / 80 cal
  renderPortion();
  openSheet("sheetPortion");
}

function renderPortion() {
  const f = portionFood, q = portionQty;
  const m = inputMode(f);
  const mk = (v, l) => `<div><b>${round(f[v] * q, v === "cal" ? 0 : 1)}</b><small>${l}</small></div>`;
  const partsNote = f.parts && f.parts.length
    ? `<p class="hint">Contains ${f.parts.length} item${f.parts.length > 1 ? "s" : ""}.</p>` : "";

  const head = m
    ? `<p class="hint">${f.per100
        ? `Per 100 g: ${f.cal} cal, ${f.p}p ${f.c}c ${f.f}f${
            S.usage[f.id]?.q ? ". Pre-filled with your last portion." : ""}`
        : `Enter the calories from the label or your best estimate. Macros are split as a typical sauce.`}</p>`
    : `<p class="hint">Per ${esc(f.unit)}: ${f.cal} cal, ${f.p}p ${f.c}c ${f.f}f${f.sv ? `. Recipe makes ${f.sv}.` : ""}</p>`;

  const shown = m ? qtyToInput(f, q) : q;
  const chips = m
    ? m.chips.map(v => `<button class="chip ${v === shown ? "on" : ""}" data-setq="${inputToQty(f, v)}">${v}${m.key === "g" ? "g" : " cal"}</button>`).join("")
    : [0.5, 1, 1.5, 2].map(v => `<button class="chip ${v === q ? "on" : ""}" data-setq="${v}">${v}x</button>`).join("");

  $("#portionBody").innerHTML = `
    <h3>${esc(f.n)}</h3>
    ${head}
    ${partsNote}
    ${partPicker ? "" : `<div class="seg">${MEALS.map(x =>
      `<button class="${x === pendingMeal ? "on" : ""}" data-meal="${x}">${x}</button>`).join("")}</div>`}
    <div class="qty-row">
      <button data-q="-">&minus;</button>
      <span class="qty-wrap">
        <input id="qtyIn" type="number" inputmode="decimal" step="${m ? m.step : 0.25}" min="0"
               value="${shown}" data-mode="${m ? m.key : ""}">
        ${m ? `<span class="qty-suffix">${m.key === "g" ? "g" : "cal"}</span>` : ""}
      </span>
      <button data-q="+">+</button>
    </div>
    <div class="chips" style="justify-content:center">${chips}</div>
    <div class="preview">${mk("cal", "cal")}${mk("p", "protein")}${mk("c", "carbs")}${mk("f", "fat")}</div>
    <button class="btn primary full" id="confirmAdd">${partPicker ? "Add to meal" : `Add to ${pendingMeal.toLowerCase()}`}</button>
    ${f.src === "recipe" && !partPicker ? `<button class="btn full" id="viewRecipe">View recipe</button>` : ""}`;
}
function commitAdd() {
  const f = portionFood, q = Number(portionQty) || 1;
  if (partPicker) {
    customParts.push({ id: f.id, qty: round(q, 2) });
    partPicker = false;
    // return to the meal builder without running the full close (which would
    // clear editingCustom and lose track of which food is being edited)
    $$(".sheet").forEach(s => { s.hidden = true; });
    renderCustom();
    openSheet("sheetCustom");
    return;
  }
  const list = S.log[curDate] || (S.log[curDate] = []);
  const m = inputMode(f);
  const disp = m ? `${qtyToInput(f, q)} ${m.key === "g" ? "g" : "cal"}` : null;
  list.push({
    fid: f.id, name: f.n, meal: pendingMeal, qty: round(q, 3), disp,
    cal: round(f.cal * q), p: round(f.p * q, 1), c: round(f.c * q, 1), f: round(f.f * q, 1),
    src: f.src,
  });
  noteUsage(f.id, round(q, 3));
  save(); closeSheets(); go("today"); renderToday();
  toast(`Added to ${pendingMeal.toLowerCase()}`);
}

function openPantry(id) {
  const f = findFood(id);
  if (!f) return;
  const idx = new Map(simpleFoods().map(x => [x.id, x]));
  const parts = f.parts ? f.parts.map(p => {
    const c = idx.get(p.id);
    const m = c ? inputMode(c) : null;
    const qs = m ? `${qtyToInput(c, p.qty)} ${m.key === "g" ? "g" : "cal"}` : `${p.qty}x`;
    return `<div class="entry">
      <div class="e-main">
        <div class="e-name">${esc(c ? c.n : "(missing)")}</div>
        <div class="e-sub">${qs}${c ? ` &middot; ${round(c.cal * p.qty)} cal, ${round(c.p * p.qty, 1)}p` : ""}</div>
      </div>
    </div>`;
  }).join("") : "";

  $("#recipeBody").innerHTML = `
    <h3>${esc(f.n)}</h3>
    <p class="hint">Per ${esc(f.unit)}: ${f.cal} cal, ${f.p}g protein, ${f.c}g carbs, ${f.f}g fat${
      f.edited ? " (your corrected values)" : ""}</p>
    <div class="preview">
      <div><b>${f.cal}</b><small>cal</small></div>
      <div><b>${f.p}</b><small>protein</small></div>
      <div><b>${f.c}</b><small>carbs</small></div>
      <div><b>${f.f}</b><small>fat</small></div>
    </div>
    <button class="btn primary full" data-logthis="${esc(f.id)}">Log this</button>
    ${f.parts ? `<h3>What's in it</h3><div class="list compact">${parts}</div>` : ""}
    <button class="btn full" data-editfood="${esc(f.id)}">Correct these numbers</button>
    <div class="mark-row">
      <button class="chip ${S.marks[f.id] === "rotation" || (S.usage[f.id]?.n || 0) > 0 ? "on" : ""}" data-mark="rotation:${esc(f.id)}">In rotation</button>
      <button class="chip ${S.marks[f.id] === "skip" ? "on" : ""}" data-mark="skip:${esc(f.id)}">Hide</button>
    </div>`;
  openSheet("sheetRecipe");
}

function openRecipe(id) {
  const r = RECIPES.find(x => x.id === id);
  if (!r) return;
  const st = statusOf(r.id);
  const times = S.usage[r.id]?.n || 0;
  const links = [];
  if (r.pdf) links.push(`<a class="btn linkbtn" href="${esc(r.pdf)}" target="_blank" rel="noopener">Open original recipe (PDF)</a>`);
  if (r.vid) links.push(`<a class="btn linkbtn" href="${esc(r.vid)}" target="_blank" rel="noopener">Watch the video</a>`);

  // Joe's ingredient lists carry sub-headings marked with "## "
  const ingHtml = r.ing.length ? r.ing.map(i =>
    i.startsWith("## ")
      ? `<li class="ing-head">${esc(i.slice(3))}</li>`
      : `<li>${esc(i)}</li>`).join("") : "";

  const basis = r.basis ? `Per ${esc(r.basis)}` : "Per serving";
  const makes = r.sv ? `. Makes ${r.sv}.` : "";

  $("#recipeBody").innerHTML = `
    <h3>${esc(r.n)}</h3>
    <p class="hint">${basis}: ${r.cal} cal &middot; ${r.p}g protein &middot; ${r.c}g carbs &middot; ${r.f}g fat${makes}${times ? ` You have logged this ${times}x.` : ""}</p>
    ${r.book ? `<p class="fine-print src-line">${esc(r.book)}${r.cat ? " &middot; " + esc(r.cat) : ""}${r.ed ? " &middot; #" + r.ed : ""}</p>` : ""}
    <div class="preview">
      <div><b>${r.ctp ?? "-"}</b><small>cal per g protein</small></div>
      <div><b>${r.sv ?? "-"}</b><small>servings</small></div>
      <div><b>${round(r.p * 4 / r.cal * 100)}%</b><small>from protein</small></div>
      <div><b>${r.st.length}</b><small>steps</small></div>
    </div>
    <button class="btn primary full" data-logthis="${esc(r.id)}">Log this</button>
    ${links.join("")}
    <div class="mark-row">
      <button class="chip ${st === "want" ? "on" : ""}" data-mark="want:${esc(r.id)}">Want to try</button>
      <button class="chip ${st === "eaten" || st === "rotation" ? "on" : ""}" data-mark="rotation:${esc(r.id)}">In rotation</button>
      <button class="chip ${st === "skip" ? "on" : ""}" data-mark="skip:${esc(r.id)}">Not for me</button>
    </div>
    ${r.blurb ? `<p class="blurb">${esc(r.blurb)}</p>` : ""}
    ${ingHtml ? `<h3>Ingredients</h3><ul class="ing-list">${ingHtml}</ul>` : ""}
    ${r.st.length ? `<h3>Instructions</h3><ol class="step-list">${r.st.map(s => `<li>${esc(s)}</li>`).join("")}</ol>` : ""}
    ${r.pdf ? `<p class="fine-print">The PDF and video open on the publisher's site and need a connection. Ingredients and steps above always work offline.</p>` : ""}`;
  openSheet("sheetRecipe");
}

/* Bundled pantry items ship with the app but must stay correctable, since a
   label number can be wrong or a product can be reformulated. */
function openEditFood(id) {
  const f = findFood(id);
  if (!f) return;
  const e = S.edits[id] || {};
  $("#customBody").innerHTML = `
    <h3>Correct ${esc(f.n)}</h3>
    <p class="hint">Per ${esc(f.unit)}. These values replace the built-in ones on this device only.</p>
    <div class="field-row">
      <label>Calories <input id="eCal" type="number" inputmode="numeric" value="${f.cal}"></label>
      <label>Protein (g) <input id="eP" type="number" inputmode="decimal" value="${f.p}"></label>
    </div>
    <div class="field-row">
      <label>Carbs (g) <input id="eC" type="number" inputmode="decimal" value="${f.c}"></label>
      <label>Fat (g) <input id="eF" type="number" inputmode="decimal" value="${f.f}"></label>
    </div>
    <button class="btn primary full" data-saveedit="${esc(id)}">Save correction</button>
    ${Object.keys(e).length ? `<button class="btn full" data-resetedit="${esc(id)}">Reset to built-in values</button>` : ""}`;
  openSheet("sheetCustom");
}

let customMode = "single";   // "single" | "meal"
let customParts = [];        // [{id, qty}] while building a meal
let editingCustom = null;
let customDraft = {};        // survives re-renders (adding a component, mode switch)

function openCustom(id) {
  editingCustom = id || null;
  const c = id ? S.custom.find(x => x.id === id) : null;
  customMode = c && c.parts && c.parts.length ? "meal" : "single";
  customParts = c && c.parts ? c.parts.map(p => ({ ...p })) : [];
  customDraft = c
    ? { n: c.n, unit: c.unit || "", cal: c.cal, p: c.p, c: c.c, f: c.f }
    : { n: "", unit: "", cal: "", p: "", c: "", f: "" };
  renderCustom();
  openSheet("sheetCustom");
}

/* The sheet re-renders when you switch modes or add a component, so pull
   whatever is typed into the draft first or it would be lost. */
function syncCustomDraft() {
  const get = sel => { const el = $(sel); return el ? el.value : undefined; };
  const map = { n: "#cName", unit: "#cUnit", cal: "#cCal", p: "#cP", c: "#cC", f: "#cF" };
  for (const [k, sel] of Object.entries(map)) {
    const v = get(sel);
    if (v !== undefined) customDraft[k] = v;
  }
}

function renderCustom() {
  const d = customDraft;
  const defUnit = customMode === "meal" ? "meal" : "serving";
  const unitV = d.unit || defUnit;

  const single = `
    <div class="field-row">
      <label>Calories <input id="cCal" type="number" inputmode="numeric" value="${esc(d.cal ?? "")}"></label>
      <label>Protein (g) <input id="cP" type="number" inputmode="decimal" value="${esc(d.p ?? "")}"></label>
    </div>
    <div class="field-row">
      <label>Carbs (g) <input id="cC" type="number" inputmode="decimal" value="${esc(d.c ?? "")}"></label>
      <label>Fat (g) <input id="cF" type="number" inputmode="decimal" value="${esc(d.f ?? "")}"></label>
    </div>`;

  const idx = new Map(simpleFoods().map(f => [f.id, f]));
  const t = mealTotals(customParts, idx);
  const partRows = customParts.length ? customParts.map((p, i) => {
    const f = idx.get(p.id);
    const m = f ? inputMode(f) : null;
    const qs = m ? `${qtyToInput(f, p.qty)} ${m.key === "g" ? "g" : "cal"}` : `${p.qty}x`;
    return `<div class="entry">
      <div class="e-main">
        <div class="e-name">${esc(f ? f.n : "(missing food)")}</div>
        <div class="e-sub">${qs}${f ? ` &middot; ${round(f.cal * p.qty)} cal, ${round(f.p * p.qty, 1)}p` : ""}</div>
      </div>
      <button class="del" data-delpart="${i}" aria-label="Remove">&times;</button>
    </div>`;
  }).join("") : `<p class="hint">Nothing added yet.</p>`;

  const meal = `
    <div class="list compact">${partRows}</div>
    <button class="add-line" id="addPart" style="margin-top:8px">+ Add a component</button>
    <div class="preview">
      <div><b>${t.cal}</b><small>cal</small></div>
      <div><b>${t.p}</b><small>protein</small></div>
      <div><b>${t.c}</b><small>carbs</small></div>
      <div><b>${t.f}</b><small>fat</small></div>
    </div>`;

  $("#customBody").innerHTML = `
    <div class="seg" style="grid-template-columns:1fr 1fr">
      <button class="${customMode === "single" ? "on" : ""}" data-cmode="single">Single food</button>
      <button class="${customMode === "meal" ? "on" : ""}" data-cmode="meal">Meal (combine)</button>
    </div>
    <label class="block">Name <input id="cName" placeholder="${customMode === "meal" ? "Sandwich meal" : "Whey shake"}" value="${esc(d.n || "")}"></label>
    <label class="block">Unit <input id="cUnit" value="${esc(unitV)}"></label>
    ${customMode === "meal" ? meal : single}
    <button class="btn primary full" id="saveCustom">${editingCustom ? "Save changes" : "Save"}</button>
    ${editingCustom ? `<button class="btn danger full" data-delcustom="${esc(editingCustom)}">Delete</button>` : ""}
    ${customMode === "meal" ? `<p class="hint">Macros update automatically if you later correct one of the components.</p>` : ""}`;
}

/* Picking a component reuses the Add sheet in a special mode. */
let partPicker = false;
function openPartPicker() {
  syncCustomDraft();
  partPicker = true;
  addScope = "all";
  $("#mealSeg").innerHTML = "";
  $("#addSearch").value = "";
  renderAddResults();
  $("#sheetCustom").hidden = true;
  openSheet("sheetAdd");
}

// ---------------------------------------------------------------- calendar
let calMonth = null;   // Date pinned to the 1st of the shown month

function openCal() {
  const d = parseKey(curDate);
  calMonth = new Date(d.getFullYear(), d.getMonth(), 1);
  renderCal();
  openSheet("sheetCal");
}
function renderCal() {
  $("#calMonth").textContent = calMonth.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  const y = calMonth.getFullYear(), m = calMonth.getMonth();
  const first = new Date(y, m, 1).getDay();
  const days = new Date(y, m + 1, 0).getDate();
  const tk = todayKey();

  let html = "";
  for (let i = 0; i < first; i++) html += `<span class="cal-cell blank"></span>`;
  for (let d = 1; d <= days; d++) {
    const k = `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const cal = (S.log[k] || []).reduce((s, e) => s + e.cal, 0);
    const future = k > tk;
    const pct = S.targets.cal ? clamp(cal / S.targets.cal, 0, 1) : 0;
    const cls = [
      "cal-cell",
      k === curDate ? "sel" : "",
      k === tk ? "today" : "",
      future ? "future" : "",
      cal ? "has" : "",
    ].filter(Boolean).join(" ");
    const ring = cal
      ? `<i class="cal-ring" style="--p:${round(pct * 100)}%;${cal > S.targets.cal ? "--rc:var(--cp-danger);" : ""}"></i>`
      : "";
    html += `<button class="${cls}" ${future ? "disabled" : `data-day="${k}"`}>${ring}<b>${d}</b>${
      S.measures[k]?.w ? `<i class="cal-dot w"></i>` : ""}</button>`;
  }
  $("#calGrid").innerHTML = html;
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
  $("#dateLabel").innerHTML = esc(prettyDate(k)) + ' <span class="caret">&#9662;</span>';
  if (curView === "today") renderToday();
  if (curView === "progress") renderProgress();
}

// ---------------------------------------------------------------- events
document.addEventListener("click", ev => {
  const el = ev.target.closest("[data-view],[data-tag],[data-sort],[data-food],[data-pick],[data-meal],[data-setq],[data-q],[data-del],[data-addmeal],[data-delcustom],[data-logthis],[data-close],[data-scope],[data-mark],[data-again],[data-day],[data-cmode],[data-delpart],[data-editcustom],[data-editfood],[data-saveedit],[data-resetedit],[data-water]");
  if (!el) return;
  const d = el.dataset;

  if (d.water) return addWater(Number(d.water));
  if (d.view) return go(d.view);
  if (d.close !== undefined) return closeSheets();
  if (d.scope) { addScope = d.scope; return renderAddResults(); }
  if (d.mark) {
    const [kind, fid] = d.mark.split(":");
    // tapping an active mark clears it; "skip" only hides from the shortlist,
    // it never discards how often you have actually eaten something
    S.marks[fid] = S.marks[fid] === kind ? undefined : kind;
    if (!S.marks[fid]) delete S.marks[fid];
    save(); openRecipe(fid);
    toast(S.marks[fid] === "rotation" ? "Added to your foods"
        : S.marks[fid] === "skip" ? "Hidden from your foods"
        : S.marks[fid] === "want" ? "Marked to try" : "Mark cleared");
    return;
  }
  if (d.tag) { cbTag = d.tag; return renderCookbook(); }
  if (d.sort) { cbSort = d.sort; return renderCookbook(); }
  if (d.food) {
    const f = findFood(d.food);
    if (!f) return;
    if (f.src === "recipe") return openRecipe(d.food);
    if (f.src === "pantry") return openPantry(d.food);
    return openPortion(d.food);
  }
  if (d.pick) return openPortion(d.pick);
  if (d.logthis) { closeSheets(); return openPortion(d.logthis); }
  if (d.meal) {
    pendingMeal = d.meal;
    if (!$("#sheetPortion").hidden) return renderPortion();
    $$("#mealSeg button").forEach(b => b.classList.toggle("on", b.dataset.meal === d.meal));
    return;
  }
  if (d.setq) { portionQty = Number(d.setq); return renderPortion(); }
  if (d.q) {
    const m = inputMode(portionFood);
    if (m) {
      const cur = qtyToInput(portionFood, portionQty);
      const next = Math.max(0, cur + (d.q === "+" ? m.step : -m.step));
      portionQty = inputToQty(portionFood, next);
    } else {
      portionQty = Math.max(0.25, round(portionQty + (d.q === "+" ? 0.25 : -0.25), 2));
    }
    return renderPortion();
  }
  if (d.addmeal) return openAdd(d.addmeal);
  if (d.again) { pendingMeal = guessMeal(); return openPortion(d.again); }
  if (d.day) { setDate(d.day); closeSheets(); return; }
  if (d.del !== undefined) {
    S.log[curDate].splice(Number(d.del), 1);
    if (!S.log[curDate].length) delete S.log[curDate];
    save(); return renderToday();
  }
  if (d.editfood) { closeSheets(); return openEditFood(d.editfood); }
  if (d.saveedit) {
    S.edits[d.saveedit] = {
      cal: +$("#eCal").value || 0, p: +$("#eP").value || 0,
      c: +$("#eC").value || 0, f: +$("#eF").value || 0,
    };
    save(); closeSheets(); renderToday(); renderMore(); toast("Corrected");
    return;
  }
  if (d.resetedit) {
    delete S.edits[d.resetedit];
    save(); closeSheets(); renderToday(); renderMore(); toast("Reset to built-in");
    return;
  }
  if (d.cmode) { syncCustomDraft(); customMode = d.cmode; return renderCustom(); }
  if (d.delpart !== undefined) { syncCustomDraft(); customParts.splice(Number(d.delpart), 1); return renderCustom(); }
  if (d.editcustom) return openCustom(d.editcustom);
  if (d.delcustom) {
    S.custom = S.custom.filter(c => c.id !== d.delcustom);
    delete S.usage[d.delcustom]; delete S.marks[d.delcustom];
    save(); closeSheets(); renderMore(); toast("Deleted");
    return;
  }
});

$("#scrim").addEventListener("click", closeSheets);
$("#fab").addEventListener("click", () => curView === "cookbook" ? openAdd() : openAdd());
$("#cbSearch").addEventListener("input", renderCookbook);
$("#addSearch").addEventListener("input", renderAddResults);

document.addEventListener("input", ev => {
  if (ev.target.id === "qtyIn") {
    const f = portionFood;
    const raw = Number(ev.target.value);
    const m = inputMode(f);
    portionQty = m ? Math.max(0, inputToQty(f, raw || 0))
                   : Math.max(0.25, raw || 1);
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
  if (id === "dateLabel") return openCal();
  if (id === "calPrev") { calMonth.setMonth(calMonth.getMonth() - 1); return renderCal(); }
  if (id === "calNext") { calMonth.setMonth(calMonth.getMonth() + 1); return renderCal(); }
  if (id === "calToday") { setDate(todayKey()); closeSheets(); return; }
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
      water: +$("#tWater").value || 100,
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
  if (id === "addPart") return openPartPicker();
  if (id === "saveCustom") {
    syncCustomDraft();
    const n = (customDraft.n || "").trim();
    if (!n) return toast("Name it first");
    const unit = (customDraft.unit || "").trim() || (customMode === "meal" ? "meal" : "serving");
    if (customMode === "meal" && !customParts.length) return toast("Add at least one component");

    const rec = editingCustom
      ? S.custom.find(c => c.id === editingCustom)
      : (S.custom[S.custom.push({ id: "c" + Date.now().toString(36) }) - 1]);
    rec.n = n; rec.unit = unit;
    if (customMode === "meal") {
      rec.parts = customParts.map(p => ({ ...p }));
      const t = mealTotals(rec.parts);
      Object.assign(rec, { cal: t.cal, p: t.p, c: t.c, f: t.f });
    } else {
      delete rec.parts;
      Object.assign(rec, {
        cal: +customDraft.cal || 0, p: +customDraft.p || 0,
        c: +customDraft.c || 0, f: +customDraft.f || 0,
      });
    }
    save(); closeSheets(); renderMore(); renderToday();
    toast(editingCustom ? "Saved" : "Food saved");
    editingCustom = null;
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
        water: d.water || {}, usage: d.usage || {}, marks: d.marks || {},
        edits: d.edits || {},
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
$("#cbSearch").setAttribute("placeholder", `Search ${foodList().length} foods...`);
setDate(todayKey());
go("today");

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}
})();
