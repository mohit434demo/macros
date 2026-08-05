import sys
from playwright.sync_api import sync_playwright

fails, errs = [], []


def check(l, c, d=""):
    print(("  PASS  " if c else "  FAIL  ") + l + ((" :: " + d) if d and not c else ""))
    if not c:
        fails.append(l)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 414, "height": 896},
                        device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("https://mohit434demo.github.io/macros/", wait_until="networkidle")
    pg.wait_for_timeout(1500)

    check("pantry data live", pg.evaluate("typeof PANTRY_ITEMS !== 'undefined'"))
    check("120 recipes mapped", pg.evaluate("Object.keys(RECIPE_NEEDS).length") == 120)
    check("ingredients cleaned",
          pg.evaluate("RECIPES.filter(r=>r.ing.length).length") == 120,
          str(pg.evaluate("RECIPES.filter(r=>r.ing.length).length")))

    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(400)
    pg.click("#pantryBtn")
    pg.wait_for_selector("#sheetPantry:not([hidden])")
    check("sheet opens", pg.locator("#pantryGroups .pchip").count() >= 80)
    for item in ["chicken", "rice", "eggs", "kimchi", "greenonion", "soy"]:
        pg.click(f"[data-pitem='{item}']")
        pg.wait_for_timeout(70)
    pg.click("#pantryApply")
    pg.wait_for_timeout(600)
    check("results render", pg.locator("#cbList .row").count() >= 3,
          str(pg.locator("#cbList .row").count()))
    check("buckets shown", pg.locator(".bucket").count() >= 1)
    pg.screenshot(path="../shots/25-live-canmake.png", full_page=True)

    ctx.set_offline(True)
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(400)
    check("works offline", pg.evaluate("Object.keys(RECIPE_NEEDS).length") == 120)
    check("selection survived offline",
          "items" in pg.inner_text("#pantryBtn"), pg.inner_text("#pantryBtn"))
    ctx.set_offline(False)

    ctx.close(); b.close()

print("js errors:", errs if errs else "none")
print("summary:", len(fails), "failures")
sys.exit(1 if fails or errs else 0)
