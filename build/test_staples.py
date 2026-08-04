"""Tests for gram-based staples, free-calorie add-ons, and the rice+chicken plate."""
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

    print("== staples bundled ==")
    check("gram staples present",
          pg.evaluate("PANTRY.filter(b=>b.per100).length") >= 20,
          str(pg.evaluate("PANTRY.filter(b=>b.per100).length")))
    check("core staples included",
          pg.evaluate("""['s-rice-white','s-chicken-thigh','s-chicken-breast','s-pasta']
                          .every(id => PANTRY.some(b=>b.id===id))"""))
    check("free-cal add-ons present", pg.evaluate("PANTRY.filter(b=>b.freeCal).length") >= 1)
    npantry = pg.evaluate("PANTRY.length")
    check("staple library expanded", npantry >= 50, f"count={npantry}")
    check("no fixed rice plate", not pg.evaluate("PANTRY.some(b=>b.id==='s-rice-chicken-plate')"))

    print("\n== rice: enter grams, not multipliers ==")
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    pg.fill("#addSearch", "white rice")
    pg.wait_for_timeout(300)
    check("row shows per-100g", "/ 100g" in pg.inner_text("#addResults"),
          pg.inner_text("#addResults")[:100])
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("input is in grams", pg.get_attribute("#qtyIn", "data-mode") == "g")
    check("defaults to 150 g", pg.input_value("#qtyIn") == "150", pg.input_value("#qtyIn"))
    check("gram suffix shown", pg.locator(".qty-suffix").inner_text() == "g")
    cal150 = int(pg.locator("#portionBody .preview b").first.inner_text())
    check("150 g of rice = 195 cal", cal150 == 195, f"got {cal150}")

    pg.fill("#qtyIn", "200")
    pg.wait_for_timeout(250)
    cal200 = int(pg.locator("#portionBody .preview b").first.inner_text())
    check("200 g scales linearly", cal200 == 260, f"got {cal200}")

    pg.click("[data-setq]")   # first chip = 100 g
    pg.wait_for_timeout(250)
    check("chip sets 100 g", pg.input_value("#qtyIn") == "100", pg.input_value("#qtyIn"))
    pg.click("[data-q='+']")
    pg.wait_for_timeout(250)
    check("plus steps by 10 g", pg.input_value("#qtyIn") == "110", pg.input_value("#qtyIn"))

    print("\n== log the exact dinner ==")
    pg.fill("#qtyIn", "150")
    pg.wait_for_timeout(250)
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)
    sub = pg.locator(".entry .e-sub").first.inner_text()
    check("entry reads in grams", sub.startswith("150 g"), sub)

    pg.click("#fab")
    pg.fill("#addSearch", "chicken thigh")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    pg.fill("#qtyIn", "310")
    pg.wait_for_timeout(250)
    calc = int(pg.locator("#portionBody .preview b").first.inner_text())
    prot = float(pg.locator("#portionBody .preview b").nth(1).inner_text())
    check("310 g thigh = 648 cal", calc == 648, f"got {calc}")
    check("310 g thigh = 80.6 g protein", abs(prot - 80.6) < 0.2, f"got {prot}")
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)

    print("\n== free-calorie sauce add-on ==")
    pg.click("#fab")
    pg.fill("#addSearch", "marinade")
    pg.wait_for_timeout(300)
    check("sauce add-on findable", pg.locator("#addResults .row").count() >= 1)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("input is in calories", pg.get_attribute("#qtyIn", "data-mode") == "cal")
    check("defaults to 80 cal", pg.input_value("#qtyIn") == "80", pg.input_value("#qtyIn"))
    scal = int(pg.locator("#portionBody .preview b").first.inner_text())
    check("80 cal reads as 80", scal == 80, f"got {scal}")
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)

    total = int(pg.inner_text("#kcalEaten"))
    check("dinner totals 923 cal", total == 195 + 648 + 80, f"got {total}")
    macro = pg.inner_text("#macroBars")
    check("protein about 85 g", "85 /" in macro or "84 /" in macro, macro[:90])
    check("three entries", pg.locator(".entry").count() == 3)
    pg.screenshot(path="../shots/17-gram-dinner.png", full_page=True)

    print("\n== the plate's parts still add up ==")
    plate = pg.evaluate("""() => {
      const idx = {}; PANTRY.forEach(b => { if(!b.parts) idx[b.id]=b; });
      const rice = idx['s-rice-white'], thigh = idx['s-chicken-thigh'], sauce = idx['s-sauce-addon'];
      const cal = rice.cal*1.5 + thigh.cal*3.1 + sauce.cal*8;
      const p = rice.p*1.5 + thigh.p*3.1 + sauce.p*8;
      return {cal: Math.round(cal), p: +p.toFixed(1)};
    }""")
    print("   dinner:", plate)
    check("dinner math checks out", plate["cal"] == 923, str(plate))
    check("dinner protein", abs(plate["p"] - 84.65) < 0.5, str(plate))

    print("\n== last portion is remembered ==")
    pg.click("#fab")
    pg.fill("#addSearch", "white rice")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("rice pre-fills last 150 g", pg.input_value("#qtyIn") == "150", pg.input_value("#qtyIn"))
    pg.fill("#qtyIn", "220")
    pg.wait_for_timeout(200)
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)
    pg.click("#fab")
    pg.fill("#addSearch", "white rice")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("now pre-fills 220 g", pg.input_value("#qtyIn") == "220", pg.input_value("#qtyIn"))
    pg.click("#sheetPortion [data-close]")
    pg.wait_for_timeout(300)

    print("\n== corrections still work on staples ==")
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(300)
    pg.click("[data-tag='staple']")
    pg.wait_for_timeout(300)
    st = pg.locator("#cbList .row").count()
    check("staples filter", st >= 9, f"staples={st}")
    pg.fill("#cbSearch", "chicken thigh")
    pg.wait_for_timeout(300)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    pg.click("[data-editfood]")
    pg.wait_for_timeout(300)
    pg.fill("#eCal", "220")
    pg.click("[data-saveedit]")
    pg.wait_for_timeout(400)
    newplate = pg.evaluate("""() => {
      const foods = {};
      PANTRY.forEach(b => { if(!b.parts) foods[b.id] = {...b}; });
      const S = JSON.parse(localStorage.getItem('nt.v1'));
      Object.entries(S.edits||{}).forEach(([k,v]) => { if(foods[k]) Object.assign(foods[k], v); });
      return Math.round(foods['s-chicken-thigh'].cal * 3.1);
    }""")
    check("correction applies to gram staples", newplate == round(220 * 3.1),
          f"got {newplate}, expected {round(220 * 3.1)}")
    pg.click("[data-view='cookbook']")
    pg.fill("#cbSearch", "chicken thigh")
    pg.wait_for_timeout(300)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_timeout(300)
    pg.click("[data-editfood]")
    pg.wait_for_timeout(250)
    pg.click("[data-resetedit]")
    pg.wait_for_timeout(350)

    print("\n== persistence ==")
    pg.reload(wait_until="networkidle")
    pg.wait_for_timeout(600)
    check("entries survived", pg.locator(".entry").count() == 4)
    check("gram label survived", pg.locator(".entry .e-sub").first.inner_text().startswith("150 g"))
    check("total survived", int(pg.inner_text("#kcalEaten")) == 923 + 286)

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
