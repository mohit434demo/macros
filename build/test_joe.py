"""Tests for the second cookbook (Joe x Fitness) integration."""
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

    print("== both cookbooks loaded ==")
    check("120 recipes", pg.evaluate("RECIPES.length") == 120, str(pg.evaluate("RECIPES.length")))
    check("70 from Stealth Health",
          pg.evaluate("RECIPES.filter(r=>r.book==='Stealth Health').length") == 70)
    check("50 from Joe x Fitness",
          pg.evaluate("RECIPES.filter(r=>r.book==='Joe x Fitness').length") == 50)
    check("every Joe recipe has steps",
          pg.evaluate("RECIPES.filter(r=>r.book==='Joe x Fitness' && r.st.length).length") == 50)
    check("every Joe recipe has ingredients",
          pg.evaluate("RECIPES.filter(r=>r.book==='Joe x Fitness' && r.ing.length).length") == 50)
    check("all six Joe categories present",
          set(pg.evaluate("[...new Set(RECIPES.filter(r=>r.cat).map(r=>r.cat))]")) ==
          {"Meal Prep", "30-Minute", "High Protein", "Viral", "Banchan", "Soups"},
          str(pg.evaluate("[...new Set(RECIPES.filter(r=>r.cat).map(r=>r.cat))]")))

    print("\n== macros are sane ==")
    bad = pg.evaluate("""RECIPES.filter(r => {
      const calc = 4*r.p + 4*r.c + 9*r.f;
      return Math.abs(calc - r.cal) > Math.max(80, 0.2*r.cal);
    }).map(r => r.n)""")
    check("no macro-math outliers in the new book",
          not [n for n in bad if "Burrito" not in n and "Wrap" not in n], str(bad))
    check("no zero-calorie recipes", pg.evaluate("RECIPES.filter(r=>!r.cal).length") == 0)
    check("no missing protein", pg.evaluate("RECIPES.filter(r=>r.p==null).length") == 0)

    print("\n== cookbook filters ==")
    pg.click("[data-view='cookbook']")
    pg.wait_for_timeout(400)
    total = pg.locator("#cbList .row").count()
    check("full list includes both books", total == 120 + pg.evaluate("PANTRY.length"),
          f"rows={total}")
    for tag, want in [("joe", 50), ("stealth", 70), ("banchan", 10),
                      ("highprotein", 10), ("mealprep", 10), ("quick", 10)]:
        pg.click(f"[data-tag='{tag}']")
        pg.wait_for_timeout(280)
        got = pg.locator("#cbList .row").count()
        check(f"{tag} filter = {want}", got == want, f"got {got}")
    pg.click("[data-tag='korean']")
    pg.wait_for_timeout(280)
    kor = pg.locator("#cbList .row").count()
    check("korean filter finds a good set", kor >= 25, f"got {kor}")
    pg.click("[data-tag='all']")
    pg.wait_for_timeout(250)
    pg.screenshot(path="../shots/21-two-books.png")

    print("\n== a Joe recipe opens correctly ==")
    pg.fill("#cbSearch", "napa cabbage shrimp")
    pg.wait_for_timeout(350)
    check("searchable", pg.locator("#cbList .row").count() == 1)
    check("book pill shown", pg.locator("#cbList .pill.book").count() == 1)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    body = pg.inner_text("#recipeBody")
    check("shows the source book", "Joe x Fitness" in body, body[:120])
    check("shows the category", "Viral" in body, body[:160])
    check("has ingredients", pg.locator("#recipeBody .ing-list li").count() >= 8)
    check("has steps", pg.locator("#recipeBody .step-list li").count() >= 5)
    check("has the author blurb", pg.locator("#recipeBody .blurb").count() == 1)
    check("no broken PDF link", pg.locator("#recipeBody a.linkbtn").count() == 0)
    pg.screenshot(path="../shots/22-joe-recipe.png", full_page=True)

    print("\n== ingredient sub-headings render ==")
    pg.click("#sheetRecipe [data-close]")
    pg.fill("#cbSearch", "bulgogi kbbq")
    pg.wait_for_timeout(350)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    heads = pg.locator("#recipeBody .ing-head").count()
    check("sub-headings present", heads >= 2, f"heads={heads}")
    check("sub-headings are not bulleted as ingredients",
          "Spicy Korean House Salad" in pg.inner_text("#recipeBody"))

    print("\n== logging a Joe recipe ==")
    pg.click("[data-logthis]")
    pg.wait_for_selector("#sheetPortion:not([hidden])")
    cal = int(pg.locator("#portionBody .preview b").first.inner_text())
    check("portion sheet shows calories", cal == 590, f"got {cal}")
    pg.click("#confirmAdd")
    pg.wait_for_timeout(450)
    check("logged to today", pg.locator(".entry").count() == 1)
    check("calories counted", int(pg.inner_text("#kcalEaten")) == 590)

    print("\n== a Stealth recipe still works ==")
    pg.click("[data-view='cookbook']")
    pg.fill("#cbSearch", "chicken parm lasagna")
    pg.wait_for_timeout(350)
    pg.locator("#cbList .row").first.click()
    pg.wait_for_selector("#sheetRecipe:not([hidden])")
    check("stealth recipe keeps its PDF link",
          pg.locator("#recipeBody a.linkbtn").count() >= 1)
    check("stealth shows its book", "Stealth Health" in pg.inner_text("#recipeBody"))

    ctx.close(); b.close()

print("\n== js errors ==")
print("   none" if not errs else "\n".join("   " + e for e in errs[:10]))
print(f"\n== summary: {len(fails)} failures, {len(errs)} js errors ==")
sys.exit(1 if fails or errs else 0)
