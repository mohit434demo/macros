import json, pathlib
r = json.loads((pathlib.Path(__file__).parent.parent / "data/joe_recipes.json").read_text(encoding="utf-8"))
print("total:", len(r))

print("\n--- all recipes ---")
for i, x in enumerate(r):
    print(f" {i+1:>2}. {x['name'][:44]:<46} {x['calories']:>5} cal {x['protein']:>5}p "
          f"{x['carbs']:>5}c {x['fat']:>5}f  ctp={x['ctp']:<5} {x['category'][:12]:<13} "
          f"ing={len(x['ingredients']):>2} st={len(x['steps']):>2}  p{x['page']}")

print("\n--- macro math outliers ---")
bad = 0
for x in r:
    calc = 4 * x["protein"] + 4 * x["carbs"] + 9 * x["fat"]
    d = calc - x["calories"]
    if abs(d) > max(70, 0.18 * x["calories"]):
        bad += 1
        print(f"   {x['name'][:40]:<42} stated={x['calories']:>5} calc={calc:>6.0f} diff={d:+.0f}")
print("   outliers:", bad)

print("\n--- missing steps ---")
for x in r:
    if not x["steps"]:
        print("   ", x["name"], "page", x["page"])

print("\n--- suspicious titles ---")
for x in r:
    n = x["name"]
    if len(n) < 5 or len(n) > 52 or any(k in n.lower() for k in ["macros", "ingredient", "calorie"]):
        print("   ", repr(n), "page", x["page"])

print("\n--- sample detail ---")
s = r[0]
print("NAME:", s["name"], "| basis:", s["basis"], "| servings:", s["servings"])
print("BLURB:", s["blurb"][:200])
print("INGREDIENTS:")
for i in s["ingredients"][:14]:
    print("   ", i)
print("STEPS:")
for i in s["steps"][:4]:
    print("   -", i[:120])
