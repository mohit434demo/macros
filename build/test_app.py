"""Drive the PWA in a phone-sized browser and assert core flows work."""
import sys, pathlib
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8777/index.html"
SHOTS = pathlib.Path(__file__).parent.parent / "shots"
SHOTS.mkdir(exist_ok=True)

errors, failures = [], []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (" :: " + detail if detail and not cond else ""))
    if not cond:
        failures.append(label + (" :: " + detail if detail else ""))


with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 414, "height": 896},
                        device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))

    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_timeout(400)

    print("\n== boot ==")
    check("recipes loaded", pg.evaluate("typeof RECIPES !== 'undefined' && RECIPES.length") == 70,
          str(pg.evaluate("typeof RECIPES !== 'undefined' ? RECIPES.length : 'undefined'")))
    check("title is Today", pg.inner_text("#viewTitle").strip() == "Today")
    check("target shows 1875", pg.inner_text("#kcalTarget").strip() == "1875",
          pg.inner_text("#kcalTarget"))
    check("four meals rendered", pg.locator(".meal").count() == 4)
    pg.screenshot(path=str(SHOTS / "01-today-empty.png"))

    print("\n== log a food ==")
    pg.click("#fab")
    pg.wait_for_selector("#sheetAdd:not([hidden])")
    pg.fill("#addSearch", "chicken parm")
    pg.wait_for_timeout(250)
    n = pg.locator("#addResults .row").count()
    check("search returns results", n >= 1, f"count={n}")
    pg.screenshot(path=str(SHOTS / "02-search.png"))
    pg.locator("#addResults .row").first.click()
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    pg.screenshot(path=str(SHOTS / "03-portion.png"))

    base_cal = int(pg.locator("#portionBody .preview b").first.inner_text())
    pg.click("[data-setq='1.5']")
    pg.wait_for_timeout(150)
    scaled = int(pg.locator("#portionBody .preview b").first.inner_text())
    check("1.5x scales calories", scaled == round(base_cal * 1.5), f"{base_cal} -> {scaled}")

    pg.click("#confirmAdd")
    pg.wait_for_timeout(350)
    check("entry appears on Today", pg.locator(".entry").count() == 1)
    eaten = int(pg.inner_text("#kcalEaten"))
    check("calories counted", eaten == scaled, f"eaten={eaten} expected={scaled}")
    left = int(pg.inner_text("#kcalLeft"))
    check("remaining math", left == 1875 - scaled, f"left={left}")
    pg.screenshot(path=str(SHOTS / "04-today-logged.png"))

    print("\n== persistence ==")
    pg.reload(wait_until="networkidle")
    pg.wait_for_timeout(400)
    check("entry survives reload", pg.locator(".entry").count() == 1)
    check("totals survive reload", int(pg.inner_text("#kcalEaten")) == scaled)

    print("\n== cookbook ==")
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(300)
    total = pg.locator("#cbList .row").count()
    expect_total = pg.evaluate("RECIPES.length + PANTRY.length")
    check("all foods listed", total == expect_total, f"count={total} expected={expect_total}")
    pg.click("[data-tag='beef']")
    pg.wait_for_timeout(250)
    beef = pg.locator("#cbList .row").count()
    check("beef filter narrows", 0 < beef < total, f"beef={beef}")
    pg.click("[data-tag='all']")
    pg.click("[data-sort='ctp']")
    pg.wait_for_timeout(250)
    badges = [pg.locator("#cbList .row .badge").nth(i).inner_text() for i in range(3)]
    vals = [float(x) for x in badges if x != "-"]
    check("ctp sort ascending", vals == sorted(vals), str(badges))
    pg.screenshot(path=str(SHOTS / "05-cookbook.png"))

    # open a recipe specifically (pantry items sort ahead of some recipes)
    rid = pg.evaluate("RECIPES.find(r => r.ing.length && r.st.length).id")
    pg.evaluate(f"document.querySelector('[data-food=\"{rid}\"]')?.scrollIntoView()")
    pg.click(f"[data-food='{rid}']")
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    ing = pg.locator("#recipeBody .ing-list li").count()
    st = pg.locator("#recipeBody .step-list li").count()
    check("recipe has ingredients", ing > 0, f"ing={ing}")
    check("recipe has steps", st > 0, f"steps={st}")
    pg.screenshot(path=str(SHOTS / "06-recipe.png"))
    pg.click("#sheetRecipe [data-close]")

    print("\n== progress + adaptive tdee ==")
    pg.evaluate("""() => {
      const KEY='nt.v1'; const S=JSON.parse(localStorage.getItem(KEY));
      const d=new Date(); S.measures={}; S.log=S.log||{};
      for (let i=27;i>=0;i--){
        const dt=new Date(d); dt.setDate(dt.getDate()-i);
        const k=dt.getFullYear()+'-'+String(dt.getMonth()+1).padStart(2,'0')+'-'+String(dt.getDate()).padStart(2,'0');
        S.measures[k]={w: 185 - (27-i)*0.14 + (i%3===0?0.4:-0.3), waist: 36 - (27-i)*0.02};
        S.log[k]=[{fid:'x',name:'Test day',meal:'Lunch',qty:1,cal:1875,p:140,c:212,f:52,src:'custom'}];
      }
      localStorage.setItem(KEY, JSON.stringify(S));
    }""")
    pg.reload(wait_until="networkidle")
    pg.click("[data-view='progress']")
    pg.wait_for_timeout(500)
    check("weight chart drawn", pg.locator("#weightChart svg").count() == 1)
    check("waist chart drawn", pg.locator("#waistChart svg").count() == 1)
    tdee_txt = pg.inner_text("#tdeeBox")
    check("tdee estimated", "estimated maintenance" in tdee_txt, tdee_txt[:120])
    stats = pg.inner_text("#progStats")
    check("trend weight shown", "Trend weight" in stats)
    pg.screenshot(path=str(SHOTS / "07-progress.png"), full_page=True)
    print("  tdee box:", " ".join(tdee_txt.split())[:220])

    print("\n== settings ==")
    pg.click("[data-view='more']")
    pg.wait_for_timeout(250)
    pg.click("#recalc")
    pg.wait_for_timeout(300)
    note = pg.inner_text("#calcNote")
    check("recalc produces note", "maintenance" in note, note[:100])
    print("  calcNote:", " ".join(note.split()))
    pg.screenshot(path=str(SHOTS / "08-settings.png"), full_page=True)

    print("\n== dark mode ==")
    pg.click("[data-view='today']")
    pg.click("#themeBtn")
    pg.wait_for_timeout(300)
    check("theme toggles to dark", pg.evaluate("document.documentElement.getAttribute('data-theme')") == "dark")
    pg.screenshot(path=str(SHOTS / "09-dark.png"))
    pg.click("#themeBtn")

    print("\n== service worker ==")
    pg.wait_for_timeout(1200)
    sw = pg.evaluate("navigator.serviceWorker.controller ? 'active' : (navigator.serviceWorker.getRegistrations().then(r=>r.length), 'registering')")
    regs = pg.evaluate("navigator.serviceWorker.getRegistrations().then(r => r.length)")
    check("service worker registered", regs >= 1, f"regs={regs}")

    ctx.close(); b.close()

print("\n==== console errors ====")
if errors:
    for e in errors[:20]:
        print("  ", e)
else:
    print("   none")

print("\n==== summary ====")
print(f"   failures: {len(failures)}   js errors: {len(errors)}")
for f in failures:
    print("   FAIL:", f)
sys.exit(1 if failures or errors else 0)
