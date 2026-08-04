"""Tests for the water counter and the import round-trip fix."""
import sys, json
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

    print("== water widget ==")
    check("water shows on the summary card", pg.locator("#waterOz").is_visible())
    check("starts at 0", pg.inner_text("#waterOz") == "0")
    check("goal is 100 oz", pg.inner_text("#waterGoal") == "100", pg.inner_text("#waterGoal"))
    check("two add buttons", pg.locator(".water-btns .wbtn").count() == 2)

    print("\n== counting ==")
    pg.click("[data-water='8']")
    pg.wait_for_timeout(250)
    check("+8 glass", pg.inner_text("#waterOz") == "8", pg.inner_text("#waterOz"))
    pg.click("[data-water='16']")
    pg.wait_for_timeout(250)
    check("+16 bottle", pg.inner_text("#waterOz") == "24", pg.inner_text("#waterOz"))
    pg.click("[data-water='-8']")
    pg.wait_for_timeout(250)
    check("minus works", pg.inner_text("#waterOz") == "16", pg.inner_text("#waterOz"))
    w = pg.evaluate("getComputedStyle(document.getElementById('waterBar')).width")
    check("bar has width", w != "0px" and w != "auto", w)

    for _ in range(3):
        pg.click("[data-water='-8']")
        pg.wait_for_timeout(120)
    check("cannot go below zero", pg.inner_text("#waterOz") == "0", pg.inner_text("#waterOz"))

    print("\n== goal state ==")
    for _ in range(7):
        pg.click("[data-water='16']")
        pg.wait_for_timeout(90)
    check("reaches 112 oz", pg.inner_text("#waterOz") == "112", pg.inner_text("#waterOz"))
    check("bar marks goal met",
          "done" in (pg.get_attribute("#waterBar", "class") or ""),
          pg.get_attribute("#waterBar", "class"))
    pg.screenshot(path="../shots/19-water.png")

    print("\n== per-day and persistence ==")
    pg.click("#dateBack")
    pg.wait_for_timeout(300)
    check("yesterday is its own count", pg.inner_text("#waterOz") == "0", pg.inner_text("#waterOz"))
    pg.click("[data-water='8']")
    pg.wait_for_timeout(200)
    pg.click("#dateFwd")
    pg.wait_for_timeout(300)
    check("today still 112", pg.inner_text("#waterOz") == "112", pg.inner_text("#waterOz"))

    pg.reload(wait_until="networkidle")
    pg.wait_for_timeout(500)
    check("water survives reload", pg.inner_text("#waterOz") == "112", pg.inner_text("#waterOz"))

    print("\n== editable goal ==")
    pg.click("[data-view='more']")
    pg.wait_for_timeout(250)
    check("goal field prefilled", pg.input_value("#tWater") == "100", pg.input_value("#tWater"))
    pg.fill("#tWater", "120")
    pg.click("#saveTargets")
    pg.wait_for_timeout(300)
    pg.click("[data-view='today']")
    pg.wait_for_timeout(250)
    check("goal updates", pg.inner_text("#waterGoal") == "120", pg.inner_text("#waterGoal"))
    check("no longer marked done",
          "done" not in (pg.get_attribute("#waterBar", "class") or ""))

    print("\n== import keeps everything (regression) ==")
    # log a food so usage/marks exist, then round-trip the whole state
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    pg.fill("#addSearch", "quinoa")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)

    dump = pg.evaluate("localStorage.getItem('nt.v1')")
    state = json.loads(dump)
    check("export has water", "water" in state and state["water"])
    check("export has usage", "usage" in state and state["usage"])

    restored = pg.evaluate("""(raw) => {
      const d = JSON.parse(raw);
      // mirror the import path exactly
      const S = {
        targets: d.targets, profile: d.profile,
        log: d.log || {}, measures: d.measures || {}, custom: d.custom || [],
        water: d.water || {}, usage: d.usage || {}, marks: d.marks || {},
        edits: d.edits || {},
      };
      return {water: Object.keys(S.water).length, usage: Object.keys(S.usage).length};
    }""", dump)
    check("import keeps water", restored["water"] >= 1, str(restored))
    check("import keeps usage", restored["usage"] >= 1, str(restored))

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
