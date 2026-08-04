"""Verify the gram staples on the deployed site."""
import sys
from playwright.sync_api import sync_playwright

BASE = "https://mohit434demo.github.io/macros/"
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
    pg.wait_for_timeout(1200)

    check("gram staples live", pg.evaluate("PANTRY.filter(b=>b.per100).length") == 4)
    check("add-ons live", pg.evaluate("PANTRY.filter(b=>(b.tags||[]).includes('addon')).length") >= 5)
    check("rice plate live", pg.evaluate("PANTRY.some(b=>b.id==='s-rice-chicken-plate')"))

    print("\n== log the real dinner on the live site ==")
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    pg.fill("#addSearch", "white rice")
    pg.wait_for_timeout(350)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("grams input", pg.get_attribute("#qtyIn", "data-mode") == "g")
    pg.fill("#qtyIn", "150")
    pg.wait_for_timeout(250)
    check("150 g rice = 195", int(pg.locator("#portionBody .preview b").first.inner_text()) == 195)
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)

    pg.click("#fab")
    pg.fill("#addSearch", "chicken thigh")
    pg.wait_for_timeout(350)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    pg.fill("#qtyIn", "310")
    pg.wait_for_timeout(250)
    check("310 g thigh = 648", int(pg.locator("#portionBody .preview b").first.inner_text()) == 648)
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)

    pg.click("#fab")
    pg.fill("#addSearch", "marinade")
    pg.wait_for_timeout(350)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("calorie input", pg.get_attribute("#qtyIn", "data-mode") == "cal")
    pg.fill("#qtyIn", "80")
    pg.wait_for_timeout(250)
    pg.click("#confirmAdd")
    pg.wait_for_timeout(500)

    total = int(pg.inner_text("#kcalEaten"))
    check("dinner totals 923", total == 923, f"got {total}")
    check("entries read in grams",
          pg.locator(".entry .e-sub").first.inner_text().startswith("150 g"),
          pg.locator(".entry .e-sub").first.inner_text())
    pg.screenshot(path="../shots/18-live-dinner.png", full_page=True)

    print("\n== offline still works ==")
    ctx.set_offline(True)
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    check("loads offline", pg.locator(".meal").count() == 4)
    check("staples offline", pg.evaluate("typeof PANTRY!=='undefined' && PANTRY.length") >= 18)
    check("data intact offline", int(pg.inner_text("#kcalEaten")) == 923)
    ctx.set_offline(False)

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
