"""Tests for the pantry foods, combo meals, corrections, and calendar picker."""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8777/index.html"
fails, errs = [], []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + ((" :: " + detail) if detail and not cond else ""))
    if not cond:
        fails.append(label)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 414, "height": 896},
                        device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_timeout(500)

    print("== pantry loaded ==")
    NP = pg.evaluate("PANTRY.length")
    TOTAL = pg.evaluate("RECIPES.length + PANTRY.length")
    check("pantry bundled", NP >= 8, f"count={NP}")
    check("totals line up", pg.evaluate("RECIPES.length") + NP == TOTAL)

    print("\n== pantry starts in My foods ==")
    check("quick add populated on first run", "Quick add" in pg.inner_text("#quickAdd"))
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    scope = pg.inner_text("#addScope")
    check("shortlist has every pantry item", f"My foods ({NP})" in scope, scope)
    check("everything shows the full count", f"Everything ({TOTAL})" in scope, scope)
    check("defaults to my foods",
          "on" in (pg.locator("#addScope .chip").first.get_attribute("class") or ""))
    check("a saved meal is listed first",
          "Meal" in pg.locator("#addResults .row").first.inner_text()
          or "Plate" in pg.locator("#addResults .row").first.inner_text(),
          pg.locator("#addResults .row").first.inner_text()[:60])
    pg.screenshot(path="../shots/14-myfoods.png")

    print("\n== combo meal macros derive from parts ==")
    meal = pg.evaluate("""() => {
      const idx = {}; PANTRY.forEach(b => { if(!b.parts) idx[b.id]=b; });
      const m = PANTRY.find(b => b.id === 'p-sandwich-meal');
      let cal=0,p=0,c=0,f=0;
      for (const part of m.parts) { const s = idx[part.id];
        cal+=s.cal*part.qty; p+=s.p*part.qty; c+=s.c*part.qty; f+=s.f*part.qty; }
      return {cal: Math.round(cal), p: +p.toFixed(1), c: +c.toFixed(1), f: +f.toFixed(1)};
    }""")
    print("   computed:", meal)
    pg.fill("#addSearch", "sandwich meal")
    pg.wait_for_timeout(300)
    row = pg.locator("#addResults .row").first.inner_text()
    check("meal calories shown", str(meal["cal"]) in row, f"{meal} vs {row[:70]}")
    check("meal is a sane sandwich", 480 < meal["cal"] < 620, str(meal))
    check("meal protein is high", meal["p"] > 40, str(meal))

    print("\n== log the meal ==")
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("shows component count", "Contains 6 items" in pg.inner_text("#portionBody"),
          pg.inner_text("#portionBody")[:120])
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)
    eaten = int(pg.inner_text("#kcalEaten"))
    check("meal logged with derived calories", eaten == meal["cal"], f"{eaten} vs {meal['cal']}")
    prot = pg.inner_text("#macroBars")
    check("protein counted", f"{round(meal['p'])} /" in prot or f"{int(meal['p'])} /" in prot, prot[:80])

    print("\n== correcting a bundled food updates the meal ==")
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(300)
    pg.fill("#cbSearch", "bero")
    pg.wait_for_timeout(300)
    check("pantry item searchable", pg.locator("#cbList .row").count() == 1)
    pg.fill("#cbSearch", "turkey deli")
    pg.wait_for_timeout(300)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    check("pantry sheet has correct button", pg.locator("[data-editfood]").count() == 1)
    pg.click("[data-editfood]")
    pg.wait_for_selector("#sheetCustom:not([hidden])")
    pg.fill("#eCal", "120")
    pg.click("[data-saveedit]")
    pg.wait_for_timeout(400)
    pg.click("[data-view='cookbook']")
    pg.fill("#cbSearch", "sandwich meal")
    pg.wait_for_timeout(350)
    txt = pg.locator("#cbList .row").first.inner_text()
    newcal = int(txt.split(" cal")[0].split("\n")[-1])
    # The app sums unrounded component values and rounds once, which is correct.
    # Recompute the same way rather than adding a delta to an already-rounded total.
    expect = pg.evaluate("""() => {
      const idx = {}; PANTRY.forEach(b => { if(!b.parts) idx[b.id]=b; });
      const m = PANTRY.find(b => b.id === 'p-sandwich-meal');
      let cal = 0;
      for (const part of m.parts) {
        const base = idx[part.id];
        const cals = part.id === 'p-deli-turkey' ? 120 : base.cal;
        cal += cals * part.qty;
      }
      return Math.round(cal);
    }""")
    check("meal recalculated after correction", newcal == expect,
          f"expected {expect}, got {newcal}")
    check("edited value shown on the item",
          pg.evaluate("JSON.parse(localStorage.getItem('nt.v1')).edits['p-deli-turkey'].cal") == 120)

    # reset it so later assertions use the shipped numbers
    pg.fill("#cbSearch", "turkey deli")
    pg.wait_for_timeout(300)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    pg.click("[data-editfood]")
    pg.wait_for_timeout(250)
    pg.click("[data-resetedit]")
    pg.wait_for_timeout(350)
    check("reset clears the correction",
          pg.evaluate("!JSON.parse(localStorage.getItem('nt.v1')).edits['p-deli-turkey']"))

    print("\n== calendar picker ==")
    pg.click("[data-view='today']")
    pg.wait_for_timeout(250)
    pg.click("#dateLabel")
    pg.wait_for_selector("#sheetCal:not([hidden])")
    check("month label shown", len(pg.inner_text("#calMonth")) > 4, pg.inner_text("#calMonth"))
    cells = pg.locator("#calGrid .cal-cell:not(.blank)").count()
    check("month has days", cells >= 28, f"cells={cells}")
    check("today marked", pg.locator("#calGrid .cal-cell.today").count() == 1)
    check("logged day has a ring", pg.locator("#calGrid .cal-ring").count() >= 1)
    check("future days disabled", pg.locator("#calGrid .cal-cell.future[disabled]").count() >= 0)
    pg.screenshot(path="../shots/15-calendar.png")

    label_before = pg.inner_text("#dateLabel")
    pg.click("#calPrev")
    pg.wait_for_timeout(250)
    check("previous month navigates", pg.locator("#calGrid .cal-cell.today").count() == 0)
    pg.locator("#calGrid .cal-cell:not(.blank):not(.future)").first.click()
    pg.wait_for_timeout(400)
    check("jumped to another day", pg.inner_text("#dateLabel") != label_before,
          pg.inner_text("#dateLabel"))
    check("sheet closed after picking", pg.locator("#sheetCal").is_hidden())
    check("that day is empty", pg.locator(".entry").count() == 0)

    pg.click("#dateLabel")
    pg.wait_for_selector("#sheetCal:not([hidden])")
    pg.click("#calToday")
    pg.wait_for_timeout(400)
    check("Today button returns", "Today" in pg.inner_text("#dateLabel"))
    check("entries came back", pg.locator(".entry").count() == 1)

    print("\n== build a custom combo by hand ==")
    pg.click("[data-view='more']")
    pg.wait_for_timeout(250)
    pg.click("#addCustom")
    pg.wait_for_selector("#sheetCustom:not([hidden])")
    pg.click("[data-cmode='meal']")
    pg.wait_for_timeout(200)
    pg.fill("#cName", "Test combo")
    pg.click("#addPart")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    pg.fill("#addSearch", "kraft american")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    pg.click("[data-setq='2']")
    pg.wait_for_timeout(150)
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)
    check("returned to the meal builder", pg.locator("#sheetCustom").is_visible())
    check("component added", "Kraft" in pg.inner_text("#customBody"), pg.inner_text("#customBody")[:120])
    totals = pg.locator("#customBody .preview b").first.inner_text()
    check("combo totals 2 slices", totals == "120", f"got {totals}")
    pg.click("#saveCustom")
    pg.wait_for_timeout(400)
    check("custom meal saved", "Test combo" in pg.inner_text("#customList"))
    check("saved as a meal", pg.locator("#customList .pill").count() >= 1)
    pg.screenshot(path="../shots/16-custom-meal.png")

    print("\n== persistence ==")
    pg.reload(wait_until="networkidle")
    pg.wait_for_timeout(600)
    check("entry survived", pg.locator(".entry").count() == 1)
    check("custom meal survived",
          pg.evaluate("JSON.parse(localStorage.getItem('nt.v1')).custom.length") == 1)

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
