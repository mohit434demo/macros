"""Tests for the What can I make pantry matcher."""
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
    pg.wait_for_timeout(600)

    print("== data loaded ==")
    check("pantry items bundled", pg.evaluate("PANTRY_ITEMS.length") >= 80,
          str(pg.evaluate("typeof PANTRY_ITEMS!=='undefined' ? PANTRY_ITEMS.length : 'undef'")))
    check("all 120 recipes mapped", pg.evaluate("Object.keys(RECIPE_NEEDS).length") == 120,
          str(pg.evaluate("Object.keys(RECIPE_NEEDS).length")))
    check("staples flagged", pg.evaluate("PANTRY_ITEMS.filter(i=>i.s).length") >= 20)
    check("no recipe needs an unknown item",
          pg.evaluate("""(() => {
            const ids = new Set(PANTRY_ITEMS.map(i=>i.id));
            return Object.values(RECIPE_NEEDS).every(v => v.every(x => ids.has(x)));
          })()"""))

    print("\n== entry point ==")
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(400)
    check("button present", pg.locator("#pantryBtn").is_visible())
    pg.click("#pantryBtn")
    pg.wait_for_selector("#sheetPantry:not([hidden])")
    check("groups rendered", pg.locator("#pantryGroups h3").count() >= 5,
          str(pg.locator("#pantryGroups h3").count()))
    chips = pg.locator("#pantryGroups .pchip").count()
    check("all items shown as chips", chips == pg.evaluate("PANTRY_ITEMS.length"), f"{chips}")
    on = pg.locator("#pantryGroups .pchip.on").count()
    check("staples pre-checked", on == pg.evaluate("PANTRY_ITEMS.filter(i=>i.s).length"), f"on={on}")

    print("\n== with only staples, few recipes are ready ==")
    pg.click("#pantryApply")
    pg.wait_for_timeout(500)
    ready = pg.evaluate("""(() => {
      const h = new Set(PANTRY_ITEMS.filter(i=>i.s).map(i=>i.id));
      return RECIPES.filter(r => (RECIPE_NEEDS[r.id]||[]).every(x=>h.has(x))).length;
    })()""")
    print("   ready with staples only:", ready)
    check("staples alone unlock very little", ready <= 6, f"ready={ready}")
    check("filter chips hidden in this view", pg.locator("#cbChips").is_hidden())

    print("\n== ticking ingredients changes the answer ==")
    pg.click("#pantryBtn")     # toggles back to normal
    pg.wait_for_timeout(250)
    pg.click("#pantryBtn")     # reopen the sheet
    pg.wait_for_selector("#sheetPantry:not([hidden])")
    for item in ["chicken", "rice", "greekyog", "cheddar", "tortilla", "onion",
                 "greenonion", "salsa", "beans", "eggs", "pasta", "tomatopaste"]:
        pg.click(f"[data-pitem='{item}']")
        pg.wait_for_timeout(60)
    picked = pg.locator("#pantryGroups .pchip.on").count()
    check("selections registered", picked >= pg.evaluate("PANTRY_ITEMS.filter(i=>i.s).length") + 10,
          f"picked={picked}")
    pg.click("#pantryApply")
    pg.wait_for_timeout(600)

    body = pg.inner_text("#cbList")
    check("buckets rendered", pg.locator(".bucket").count() >= 1,
          str(pg.locator(".bucket").count()))
    rows_now = pg.locator("#cbList .row").count()
    check("more recipes surface", rows_now >= 3, f"rows={rows_now}")
    check("missing items are named", "Need " in body or "Ready to cook" in body, body[:150])
    pg.screenshot(path="../shots/24-canmake.png", full_page=True)

    print("\n== ranking is correct ==")
    correct = pg.evaluate("""(() => {
      const S = JSON.parse(localStorage.getItem('nt.v1'));
      const h = new Set(S.pantry);
      const rank = RECIPES.map(r => ({
        n: r.n, miss: (RECIPE_NEEDS[r.id]||[]).filter(x=>!h.has(x)).length
      })).filter(x => x.miss <= 2).sort((a,b)=>a.miss-b.miss);
      return {zero: rank.filter(x=>!x.miss).length,
              one: rank.filter(x=>x.miss===1).length,
              two: rank.filter(x=>x.miss===2).length};
    })()""")
    print("   buckets:", correct)
    shown = pg.locator("#cbList .row").count()
    check("shown count matches computed", shown == correct["zero"] + correct["one"] + correct["two"],
          f"shown={shown} expected={correct}")

    print("\n== a listed recipe really is satisfiable ==")
    verified = pg.evaluate("""(() => {
      const S = JSON.parse(localStorage.getItem('nt.v1'));
      const h = new Set(S.pantry);
      const first = [...document.querySelectorAll('#cbList .row')][0];
      if (!first) return null;
      const id = first.dataset.food;
      const need = RECIPE_NEEDS[id] || [];
      return {id, missing: need.filter(x=>!h.has(x))};
    })()""")
    check("top recipe has nothing missing", verified and not verified["missing"], str(verified))

    print("\n== opening a result still works ==")
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    check("recipe sheet opens", pg.locator("#recipeBody .ing-list li").count() >= 3)
    pg.click("#sheetRecipe [data-close]")
    pg.wait_for_timeout(250)

    print("\n== persistence + clear ==")
    pg.reload(wait_until="networkidle")
    pg.wait_for_timeout(600)
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(300)
    check("pantry count persists", "items" in pg.inner_text("#pantryBtn"),
          pg.inner_text("#pantryBtn"))
    pg.click("#pantryBtn")
    pg.wait_for_selector("#sheetPantry:not([hidden])")
    check("selections restored", pg.locator("#pantryGroups .pchip.on").count() == picked,
          str(pg.locator("#pantryGroups .pchip.on").count()))
    pg.click("#pantryClear")
    pg.wait_for_timeout(350)
    check("clear resets to staples",
          pg.locator("#pantryGroups .pchip.on").count() == pg.evaluate("PANTRY_ITEMS.filter(i=>i.s).length"))

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
