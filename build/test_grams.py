"""Tests for logging a food by weight when its serving size is known."""
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

    print("== create the frozen chicken patty (112 g, 180 cal) ==")
    pg.click("[data-view='more']")
    pg.wait_for_timeout(300)
    pg.click("#addCustom")
    pg.wait_for_selector("#sheetCustom:not([hidden])")
    check("serving weight field exists", pg.locator("#cGw").count() == 1)
    pg.fill("#cName", "Frozen chicken patty")
    pg.fill("#cUnit", "patty")
    pg.fill("#cCal", "180")
    pg.fill("#cP", "22")
    pg.fill("#cC", "10")
    pg.fill("#cF", "6")
    pg.fill("#cGw", "112")
    pg.click("#saveCustom")
    pg.wait_for_timeout(450)
    check("saved with weight",
          pg.evaluate("JSON.parse(localStorage.getItem('nt.v1')).custom[0].gw") == 112)

    print("\n== the exact case: ate 154 g ==")
    pg.click("[data-view='today']")
    pg.wait_for_timeout(250)
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    pg.fill("#addSearch", "frozen chicken patty")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("unit toggle shown", pg.locator("[data-punit]").count() == 2)
    check("defaults to servings", pg.get_attribute("#qtyIn", "data-mode") == "")
    check("mentions the weight", "112 g" in pg.inner_text("#portionBody"),
          pg.inner_text("#portionBody")[:140])

    pg.click("[data-punit='g']")
    pg.wait_for_timeout(300)
    check("switches to grams", pg.get_attribute("#qtyIn", "data-mode") == "g")
    check("one serving shows as 112 g", pg.input_value("#qtyIn") == "112",
          pg.input_value("#qtyIn"))

    pg.fill("#qtyIn", "154")
    pg.wait_for_timeout(300)
    cal = int(pg.locator("#portionBody .preview b").first.inner_text())
    pro = float(pg.locator("#portionBody .preview b").nth(1).inner_text())
    # 154/112 = 1.375  ->  180*1.375 = 247.5 -> 248 ;  22*1.375 = 30.25 -> 30.3
    check("154 g gives 248 cal", cal == 248, f"got {cal}")
    check("154 g gives 30.3 g protein", abs(pro - 30.3) < 0.15, f"got {pro}")

    pg.click("#confirmAdd")
    pg.wait_for_timeout(450)
    sub = pg.locator(".entry .e-sub").first.inner_text()
    check("entry reads in grams", sub.startswith("154 g"), sub)
    check("day total correct", int(pg.inner_text("#kcalEaten")) == 248,
          pg.inner_text("#kcalEaten"))

    print("\n== it reopens in grams next time ==")
    pg.click("#fab")
    pg.fill("#addSearch", "frozen chicken patty")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("opened the right food", "patty" in pg.inner_text("#portionBody").lower(),
          pg.inner_text("#portionBody")[:60])
    check("remembers grams mode", pg.get_attribute("#qtyIn", "data-mode") == "g")
    check("remembers 154 g", pg.input_value("#qtyIn") == "154", pg.input_value("#qtyIn"))

    print("\n== toggling back and forth keeps the amount ==")
    pg.click("[data-punit='serving']")
    pg.wait_for_timeout(280)
    serv = float(pg.input_value("#qtyIn"))
    check("154 g reads as 1.38 servings", abs(serv - 1.375) < 0.01, str(serv))
    cal2 = int(pg.locator("#portionBody .preview b").first.inner_text())
    check("calories unchanged by the toggle", cal2 == 248, f"got {cal2}")
    pg.click("[data-punit='g']")
    pg.wait_for_timeout(280)
    check("back to 154 g", abs(float(pg.input_value("#qtyIn")) - 154) < 1,
          pg.input_value("#qtyIn"))

    print("\n== plus and minus step sensibly in each mode ==")
    pg.click("[data-q='+']")
    pg.wait_for_timeout(250)
    check("grams step by 10", abs(float(pg.input_value("#qtyIn")) - 164) < 1,
          pg.input_value("#qtyIn"))
    pg.click("[data-punit='serving']")
    pg.wait_for_timeout(250)
    before = float(pg.input_value("#qtyIn"))
    pg.click("[data-q='+']")
    pg.wait_for_timeout(250)
    after = float(pg.input_value("#qtyIn"))
    check("servings step by 0.25", abs((after - before) - 0.25) < 0.02, f"{before} -> {after}")
    pg.click("#sheetPortion [data-close]")
    pg.wait_for_timeout(250)

    print("\n== bundled items got weights too ==")
    check("bun knows 62 g", pg.evaluate("PANTRY.find(b=>b.id==='p-dkb-white-bun').gw") == 62)
    check("cheese slice knows 21 g", pg.evaluate("PANTRY.find(b=>b.id==='p-kraft-single').gw") == 21)
    pg.click("#fab")
    pg.fill("#addSearch", "kraft american")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("cheese offers the toggle", pg.locator("[data-punit]").count() == 2)
    check("but defaults to slices", pg.get_attribute("#qtyIn", "data-mode") == "")
    pg.click("[data-punit='g']")
    pg.wait_for_timeout(250)
    pg.fill("#qtyIn", "42")
    pg.wait_for_timeout(280)
    ccal = int(pg.locator("#portionBody .preview b").first.inner_text())
    check("42 g of cheese = 2 slices = 120 cal", ccal == 120, f"got {ccal}")
    pg.click("#sheetPortion [data-close]")
    pg.wait_for_timeout(250)

    print("\n== foods without a weight are unchanged ==")
    pg.click("#fab")
    pg.fill("#addSearch", "bero")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("no toggle without a weight", pg.locator("[data-punit]").count() == 0)
    check("still logs by serving", pg.input_value("#qtyIn") == "1", pg.input_value("#qtyIn"))
    pg.click("#sheetPortion [data-close]")
    pg.wait_for_timeout(200)

    print("\n== gram staples still grams-only ==")
    pg.click("#fab")
    pg.fill("#addSearch", "white rice")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("rice has no toggle", pg.locator("[data-punit]").count() == 0)
    check("rice still in grams", pg.get_attribute("#qtyIn", "data-mode") == "g")
    pg.fill("#qtyIn", "150")
    pg.wait_for_timeout(250)
    check("150 g rice still 195 cal",
          int(pg.locator("#portionBody .preview b").first.inner_text()) == 195)
    pg.click("#sheetPortion [data-close]")
    pg.wait_for_timeout(200)

    print("\n== retrofit a weight via the correction sheet ==")
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(300)
    pg.fill("#cbSearch", "bero")
    pg.wait_for_timeout(300)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    pg.click("[data-editfood]")
    pg.wait_for_timeout(300)
    check("correction sheet has the weight field", pg.locator("#eGw").count() == 1)
    pg.fill("#eGw", "355")
    pg.click("[data-saveedit]")
    pg.wait_for_timeout(400)
    check("weight saved as an edit",
          pg.evaluate("JSON.parse(localStorage.getItem('nt.v1')).edits['p-bero-shandy'].gw") == 355)

    print("\n== persistence ==")
    pg.reload(wait_until="networkidle")
    pg.wait_for_timeout(700)
    check("entry survived", pg.locator(".entry").count() == 1)
    check("gram label survived",
          pg.locator(".entry .e-sub").first.inner_text().startswith("154 g"))
    check("total survived", int(pg.inner_text("#kcalEaten")) == 248)
    pg.screenshot(path="../shots/26-grams-toggle.png")

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
