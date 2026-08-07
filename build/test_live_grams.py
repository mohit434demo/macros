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

    check("bundled weights live", pg.evaluate("PANTRY.find(b=>b.id==='p-dkb-white-bun').gw") == 62)

    # create the patty exactly as described
    pg.click("[data-view='more']")
    pg.wait_for_timeout(300)
    pg.click("#addCustom")
    pg.wait_for_selector("#sheetCustom:not([hidden])")
    check("weight field live", pg.locator("#cGw").count() == 1)
    pg.fill("#cName", "Frozen chicken patty")
    pg.fill("#cUnit", "patty")
    pg.fill("#cCal", "180")
    pg.fill("#cP", "22")
    pg.fill("#cC", "10")
    pg.fill("#cF", "6")
    pg.fill("#cGw", "112")
    pg.click("#saveCustom")
    pg.wait_for_timeout(500)

    pg.click("[data-view='today']")
    pg.wait_for_timeout(250)
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    pg.fill("#addSearch", "frozen chicken patty")
    pg.wait_for_timeout(350)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    pg.click("[data-punit='g']")
    pg.wait_for_timeout(300)
    pg.fill("#qtyIn", "154")
    pg.wait_for_timeout(300)
    check("154 g = 248 cal live",
          int(pg.locator("#portionBody .preview b").first.inner_text()) == 248,
          pg.locator("#portionBody .preview b").first.inner_text())
    pg.click("#confirmAdd")
    pg.wait_for_timeout(500)
    check("logged as grams", pg.locator(".entry .e-sub").first.inner_text().startswith("154 g"),
          pg.locator(".entry .e-sub").first.inner_text())
    pg.screenshot(path="../shots/27-live-grams.png")

    ctx.set_offline(True)
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)
    check("offline intact", int(pg.inner_text("#kcalEaten")) == 248)
    ctx.set_offline(False)

    ctx.close(); b.close()

print("js errors:", errs if errs else "none")
print("summary:", len(fails), "failures")
sys.exit(1 if fails or errs else 0)
