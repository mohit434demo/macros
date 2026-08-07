"""Two independent users on the live site must never see each other's data."""
import sys
from playwright.sync_api import sync_playwright

URL = "https://mohit434demo.github.io/macros/"
fails = []


def check(l, c, d=""):
    print(("  PASS  " if c else "  FAIL  ") + l + ((" :: " + d) if d and not c else ""))
    if not c:
        fails.append(l)


with sync_playwright() as pw:
    b = pw.chromium.launch()

    # two separate browser contexts == two different people's phones
    mohit = b.new_context(viewport={"width": 414, "height": 896}, is_mobile=True, has_touch=True)
    family = b.new_context(viewport={"width": 414, "height": 896}, is_mobile=True, has_touch=True)

    pm, pf = mohit.new_page(), family.new_page()
    for p in (pm, pf):
        p.goto(URL, wait_until="networkidle")
        p.wait_for_timeout(1200)

    print("== user A logs food, weight and water ==")
    pm.click("#fab")
    pm.wait_for_selector("#sheetAdd:not([hidden])")
    pm.fill("#addSearch", "white rice")
    pm.wait_for_timeout(350)
    pm.locator("#addResults .row").first.click()
    pm.wait_for_selector("#sheetPortion:not([hidden])")
    pm.fill("#qtyIn", "150")
    pm.wait_for_timeout(200)
    pm.click("#confirmAdd")
    pm.wait_for_timeout(400)
    pm.click("[data-water='16']")
    pm.wait_for_timeout(200)
    pm.click("[data-view='progress']")
    pm.wait_for_timeout(300)
    pm.fill("#inWeight", "185")
    pm.fill("#inWaist", "36")
    pm.click("#saveMeasure")
    pm.wait_for_timeout(400)
    pm.click("[data-view='today']")
    pm.wait_for_timeout(300)

    a_cal = int(pm.inner_text("#kcalEaten"))
    a_water = int(pm.inner_text("#waterOz"))
    check("user A has calories logged", a_cal > 0, str(a_cal))
    check("user A has water logged", a_water == 16, str(a_water))

    print("\n== user B is untouched ==")
    pf.reload(wait_until="networkidle")
    pf.wait_for_timeout(1200)
    check("user B sees zero calories", int(pf.inner_text("#kcalEaten")) == 0,
          pf.inner_text("#kcalEaten"))
    check("user B sees zero water", int(pf.inner_text("#waterOz")) == 0,
          pf.inner_text("#waterOz"))
    check("user B has no entries", pf.locator(".entry").count() == 0)
    pf.click("[data-view='progress']")
    pf.wait_for_timeout(400)
    check("user B has no weight history", pf.input_value("#inWeight") == "",
          repr(pf.input_value("#inWeight")))
    check("user B storage is empty",
          pf.evaluate("localStorage.getItem('nt.v1') === null"),
          str(pf.evaluate("localStorage.getItem('nt.v1')"))[:80])

    print("\n== user B logs their own, A unaffected ==")
    pf.click("[data-view='today']")
    pf.wait_for_timeout(250)
    pf.click("#fab")
    pf.wait_for_selector("#sheetAdd:not([hidden])")
    pf.fill("#addSearch", "chicken breast")
    pf.wait_for_timeout(350)
    pf.locator("#addResults .row").first.click()
    pf.wait_for_selector("#sheetPortion:not([hidden])")
    pf.fill("#qtyIn", "200")
    pf.wait_for_timeout(200)
    pf.click("#confirmAdd")
    pf.wait_for_timeout(400)
    b_cal = int(pf.inner_text("#kcalEaten"))
    check("user B has their own total", b_cal > 0 and b_cal != a_cal, f"A={a_cal} B={b_cal}")

    pm.reload(wait_until="networkidle")
    pm.wait_for_timeout(1200)
    check("user A total unchanged", int(pm.inner_text("#kcalEaten")) == a_cal,
          pm.inner_text("#kcalEaten"))
    check("user A water unchanged", int(pm.inner_text("#waterOz")) == a_water)
    check("user A still has one entry", pm.locator(".entry").count() == 1)

    print("\n== targets are per-person too ==")
    pf.click("[data-view='more']")
    pf.wait_for_timeout(300)
    pf.fill("#tCal", "2200")
    pf.click("#saveTargets")
    pf.wait_for_timeout(400)
    pm.click("[data-view='today']")
    pm.wait_for_timeout(300)
    check("user A target unchanged by B", pm.inner_text("#kcalTarget") == "1875",
          pm.inner_text("#kcalTarget"))
    check("user B target changed", pf.evaluate(
        "JSON.parse(localStorage.getItem('nt.v1')).targets.cal") == 2200)

    mohit.close(); family.close(); b.close()

print(f"\n== summary: {len(fails)} failures ==")
sys.exit(1 if fails else 0)
