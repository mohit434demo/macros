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

    check("120 recipes live", pg.evaluate("RECIPES.length") == 120, str(pg.evaluate("RECIPES.length")))
    check("Joe recipes live", pg.evaluate("RECIPES.filter(r=>r.book==='Joe x Fitness').length") == 50)
    check("all Joe recipes have steps",
          pg.evaluate("RECIPES.filter(r=>r.book==='Joe x Fitness'&&r.st.length).length") == 50)

    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(400)
    pg.click("[data-tag='joe']")
    pg.wait_for_timeout(350)
    check("joe filter works live", pg.locator("#cbList .row").count() == 50)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    check("recipe opens", pg.locator("#recipeBody .step-list li").count() >= 3)
    check("shows source book", "Joe x Fitness" in pg.inner_text("#recipeBody"))
    pg.screenshot(path="../shots/23-live-two-books.png")
    pg.click("#sheetRecipe [data-close]")

    ctx.set_offline(True)
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)
    check("offline still works", pg.locator(".meal").count() == 4)
    check("both books offline", pg.evaluate("RECIPES.length") == 120)
    ctx.set_offline(False)

    ctx.close(); b.close()

print("js errors:", errs if errs else "none")
print("summary:", len(fails), "failures")
sys.exit(1 if fails or errs else 0)
