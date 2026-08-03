"""Verify the deployed update: shortlist behaviour and that recipe links resolve."""
import sys, urllib.request
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

    print("== deployed build is current ==")
    check("pdf links shipped", pg.evaluate("RECIPES.filter(r=>r.pdf).length") == 70)
    check("video links shipped", pg.evaluate("RECIPES.filter(r=>r.vid).length") == 19)
    check("pantry shipped", pg.evaluate("typeof PANTRY!=='undefined' && PANTRY.length") == 8)
    check("sandwich meal shipped",
          pg.evaluate("PANTRY.some(b=>b.id==='p-sandwich-meal' && b.parts.length===6)"))
    check("scope control present", pg.evaluate("!!document.getElementById('addScope')"))
    check("quick add slot present", pg.evaluate("!!document.getElementById('quickAdd')"))
    check("calendar sheet present", pg.evaluate("!!document.getElementById('sheetCal')"))

    print("== calendar opens on the live site ==")
    pg.click("#dateLabel")
    pg.wait_for_selector("#sheetCal:not([hidden])")
    check("calendar renders days", pg.locator("#calGrid .cal-cell:not(.blank)").count() >= 28)
    pg.click("#sheetCal [data-close]")
    pg.wait_for_timeout(300)

    print("== shortlist flow on the live site ==")
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    check("pantry is in My foods", "My foods (8)" in pg.inner_text("#addScope"),
          pg.inner_text("#addScope"))
    pg.fill("#addSearch", "sandwich meal")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    check("meal shows components", "Contains 6 items" in pg.inner_text("#portionBody"))
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)
    eaten = int(pg.inner_text("#kcalEaten"))
    check("meal logged", 480 < eaten < 620, f"eaten={eaten}")
    check("quick add appears", "Quick add" in pg.inner_text("#quickAdd"))

    print("== sample of external links actually resolve ==")
    urls = pg.evaluate("RECIPES.filter(r=>r.pdf).slice(0,5).map(r=>r.pdf)")
    ok = 0
    for u in urls:
        try:
            req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    ok += 1
        except Exception:
            pass
    check("5 sampled PDF links return 200", ok == 5, f"{ok}/5")

    vids = pg.evaluate("RECIPES.filter(r=>r.vid).slice(0,3).map(r=>r.vid)")
    import re
    # Instagram serves both /reel/ and /reels/ permalinks
    check("video links are well formed",
          all(re.match(r"^https://www\.instagram\.com/reels?/[\w-]+/?$", v) for v in vids), str(vids))
    vok = 0
    for v in vids:
        try:
            req = urllib.request.Request(v, headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"})
            with urllib.request.urlopen(req, timeout=25) as r:
                if r.status == 200:
                    vok += 1
        except Exception as ex:
            print("     video fetch:", ex)
    check("sampled video links reachable", vok >= 2, f"{vok}/3")

    pg.screenshot(path="../shots/13-live-update.png")
    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
