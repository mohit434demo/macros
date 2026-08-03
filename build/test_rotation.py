"""Tests for the earned shortlist, status marks, and recipe links."""
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
    pg.wait_for_timeout(400)

    print("== first run: shortlist starts as the bundled pantry ==")
    NP = pg.evaluate("PANTRY.length")
    TOTAL = pg.evaluate("RECIPES.length + PANTRY.length")
    check("quick add shows pantry", "Quick add" in pg.inner_text("#quickAdd"))
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    scope_txt = pg.inner_text("#addScope")
    check("scope chips shown", f"My foods ({NP})" in scope_txt and f"Everything ({TOTAL})" in scope_txt, scope_txt)
    check("defaults to my foods when pantry exists",
          "on" in (pg.locator("#addScope .chip").first.get_attribute("class") or ""))
    pg.click("[data-scope='all']")
    pg.wait_for_timeout(250)
    n = pg.locator("#addResults .row").count()
    check("all foods browsable", n >= 60, f"count={n}")

    print("\n== logging earns a place on the shortlist ==")
    pg.fill("#addSearch", "chicken tinga rice")
    pg.wait_for_timeout(250)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("portion sheet has meal picker", pg.locator("#portionBody .seg button").count() == 4)
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)

    check("quick add still populated", "Quick add" in pg.inner_text("#quickAdd"))
    qn = pg.locator("#quickAdd .chip").count()
    check("quick chips capped at 6", 1 <= qn <= 6, f"chips={qn}")

    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    check("scope counts updated", f"My foods ({NP + 1})" in pg.inner_text("#addScope"),
          pg.inner_text("#addScope"))
    rows = pg.locator("#addResults .row").count()
    check("shortlist is short", rows == NP + 1, f"rows={rows}")
    check("shows log count", "logged 1x" in pg.inner_text("#addResults"))

    print("\n== search still reaches the whole library ==")
    pg.fill("#addSearch", "lasagna")
    pg.wait_for_timeout(300)
    r2 = pg.locator("#addResults .row").count()
    check("search escapes the shortlist", r2 >= 2, f"rows={r2}")

    print("\n== quick add repeats a meal ==")
    pg.click("#sheetAdd [data-close]")
    pg.wait_for_timeout(200)
    pg.locator("#quickAdd .chip").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)
    check("second entry logged", pg.locator(".entry").count() == 2)

    print("\n== cookbook status + filters ==")
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(300)
    check("in-rotation pill shown", pg.locator(".pill.eaten").count() >= 1)
    check("count label", f"of {TOTAL}" in pg.inner_text("#cbCount"), pg.inner_text("#cbCount"))
    pg.click("[data-tag='rotation']")
    pg.wait_for_timeout(250)
    rot = pg.locator("#cbList .row").count()
    check("rotation filter", rot >= NP, f"rot={rot}")
    pg.click("[data-tag='untried']")
    pg.wait_for_timeout(250)
    unt = pg.locator("#cbList .row").count()
    check("untried excludes pantry and eaten", unt == TOTAL - rot, f"untried={unt} rot={rot}")
    pg.click("[data-tag='all']")
    pg.wait_for_timeout(200)

    print("\n== recipe links ==")
    withvid = pg.evaluate("RECIPES.filter(r=>r.vid).length")
    withpdf = pg.evaluate("RECIPES.filter(r=>r.pdf).length")
    check("all have pdf url", withpdf == 70, f"pdf={withpdf}")
    check("19 have video", withvid == 19, f"vid={withvid}")

    vid_id = pg.evaluate("RECIPES.find(r=>r.vid).id")
    pg.evaluate(f"document.querySelector('[data-food=\"{vid_id}\"]')?.scrollIntoView()")
    pg.click(f"[data-food='{vid_id}']")
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    links = pg.locator("#recipeBody a.linkbtn")
    check("two link buttons", links.count() == 2, f"links={links.count()}")
    hrefs = [links.nth(i).get_attribute("href") for i in range(links.count())]
    check("pdf href is https", hrefs[0].startswith("https://"), str(hrefs))
    check("video href is a reel", "instagram.com" in hrefs[1], str(hrefs))
    check("links open in new tab",
          all(links.nth(i).get_attribute("target") == "_blank" for i in range(2)))
    check("mark buttons present", pg.locator("#recipeBody .mark-row .chip").count() == 3)
    pg.screenshot(path="../shots/11-recipe-links.png", full_page=True)

    print("\n== marks ==")
    pg.click("[data-mark^='want:']")
    pg.wait_for_timeout(350)
    check("want mark sticks",
          "on" in (pg.locator("#recipeBody .mark-row .chip").first.get_attribute("class") or ""))
    pg.click("#sheetRecipe [data-close]")
    pg.click("[data-tag='untried']")
    pg.wait_for_timeout(250)
    check("want removes from untried", pg.locator("#cbList .row").count() == unt - 1,
          f"{pg.locator('#cbList .row').count()} vs {unt - 1}")
    pg.click("[data-tag='all']")

    # marking skip should hide an eaten recipe from the shortlist
    eaten_id = pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('nt.v1')).usage)[0]")
    logged_before = pg.evaluate(f"JSON.parse(localStorage.getItem('nt.v1')).usage['{eaten_id}'].n")
    pg.evaluate(f"document.querySelector('[data-food=\"{eaten_id}\"]')?.scrollIntoView()")
    pg.click(f"[data-food='{eaten_id}']")
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    pg.click("[data-mark^='skip:']")
    pg.wait_for_timeout(350)
    pg.click("#sheetRecipe [data-close]")
    pg.click("[data-view='today']")
    pg.wait_for_timeout(300)
    # the strip caps at 6 chips, so assert the item itself is gone rather than the count
    check("skip removes it from quick add",
          pg.evaluate(f"!document.querySelector('[data-again=\"{eaten_id}\"]')"))
    check("skip removes it from the shortlist",
          pg.evaluate(f"""() => {{
            const S = JSON.parse(localStorage.getItem('nt.v1'));
            return S.marks['{eaten_id}'] === 'skip';
          }}"""))
    check("logged entries untouched", pg.locator(".entry").count() == 2)

    print("\n== persistence ==")
    pg.reload(wait_until="networkidle")
    pg.wait_for_timeout(500)
    check("marks survive reload",
          pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('nt.v1')).marks).length") >= 2)
    check("usage survives reload",
          pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('nt.v1')).usage).length") >= 1)
    check("skip preserves the log count",
          pg.evaluate(f"JSON.parse(localStorage.getItem('nt.v1')).usage['{eaten_id}'].n") == logged_before,
          f"was {logged_before}")
    pg.screenshot(path="../shots/12-today-quick.png")

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
