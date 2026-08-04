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

    check("water widget live", pg.locator("#waterOz").is_visible())
    check("goal 100 oz", pg.inner_text("#waterGoal") == "100", pg.inner_text("#waterGoal"))
    pg.click("[data-water='16']")
    pg.wait_for_timeout(300)
    check("+16 works live", pg.inner_text("#waterOz") == "16", pg.inner_text("#waterOz"))
    pg.click("[data-water='8']")
    pg.wait_for_timeout(250)
    check("+8 works live", pg.inner_text("#waterOz") == "24", pg.inner_text("#waterOz"))

    pg.reload(wait_until="networkidle")
    pg.wait_for_timeout(1200)
    check("persists live", pg.inner_text("#waterOz") == "24", pg.inner_text("#waterOz"))

    ctx.set_offline(True)
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    check("water offline", pg.inner_text("#waterOz") == "24", pg.inner_text("#waterOz"))
    check("app offline", pg.locator(".meal").count() == 4)
    ctx.set_offline(False)

    pg.screenshot(path="../shots/20-live-water.png")
    ctx.close(); b.close()

print("js errors:", errs if errs else "none")
print("summary:", len(fails), "failures")
sys.exit(1 if fails or errs else 0)
