"""Verify the deployed GitHub Pages build: assets, PWA install criteria, offline."""
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
    bad = []
    pg.on("response", lambda r: bad.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)

    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_timeout(1500)

    print("== deployed assets ==")
    check("no failed requests", not bad, "; ".join(bad[:4]))
    check("recipes bundled", pg.evaluate("typeof RECIPES!=='undefined' && RECIPES.length") == 70)
    check("app rendered", pg.locator(".meal").count() == 4)
    check("https", pg.url.startswith("https://"))

    print("\n== pwa install criteria ==")
    man = pg.evaluate("""async () => {
      const l = document.querySelector('link[rel=manifest]');
      if (!l) return null;
      const r = await fetch(l.href);
      return r.ok ? await r.json() : null;
    }""")
    check("manifest loads", man is not None)
    if man:
        check("has name", bool(man.get("name")))
        check("display standalone", man.get("display") == "standalone")
        check("has 192 and 512 icons",
              {i["sizes"] for i in man["icons"]} >= {"192x192", "512x512"})
        check("has maskable icon", any("maskable" in i.get("purpose", "") for i in man["icons"]))
        check("theme color sage", man.get("theme_color") == "#6b8f6b")

    icons_ok = pg.evaluate("""async () => {
      const out = {};
      for (const p of ['icons/icon-192.png','icons/icon-512.png','icons/icon-maskable.png']) {
        try { const r = await fetch(p); out[p] = r.status; } catch(e) { out[p] = 'err'; }
      }
      return out;
    }""")
    check("icons reachable", all(v == 200 for v in icons_ok.values()), str(icons_ok))

    regs = pg.evaluate("navigator.serviceWorker.getRegistrations().then(r=>r.length)")
    check("service worker registered", regs >= 1, f"regs={regs}")

    print("\n== log something, then go offline ==")
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    pg.fill("#addSearch", "tinga")
    pg.wait_for_timeout(300)
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    pg.click("#confirmAdd")
    pg.wait_for_timeout(400)
    eaten = int(pg.inner_text("#kcalEaten"))
    check("logged while online", eaten > 0, f"eaten={eaten}")

    ctx.set_offline(True)
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2000)
    check("app loads offline", pg.locator(".meal").count() == 4)
    check("recipes available offline", pg.evaluate("typeof RECIPES!=='undefined' && RECIPES.length") == 70)
    check("data intact offline", int(pg.inner_text("#kcalEaten")) == eaten)
    pg.screenshot(path="../shots/10-offline.png")
    ctx.set_offline(False)

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
