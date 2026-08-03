import json, pathlib
r = json.loads((pathlib.Path(__file__).parent.parent / "data/recipes.json").read_text(encoding="utf-8"))
print("total:", len(r))

print("\n--- macro math outliers (4p+4c+9f vs stated calories) ---")
bad = 0
for x in r:
    calc = 4 * x["protein"] + 4 * x["carbs"] + 9 * x["fat"]
    diff = calc - x["calories"]
    if abs(diff) > max(60, 0.15 * x["calories"]):
        bad += 1
        print(f"  {x['name'][:42]:<44} stated={x['calories']:>4} calc={calc:>4} diff={diff:+}")
print("  outliers:", bad)

print("\n--- duplicate names ---")
seen = {}
for x in r:
    seen.setdefault(x["name"].lower(), []).append(x)
for k, v in seen.items():
    if len(v) > 1:
        print("  ", k, [(y["calories"], y["servings"]) for y in v])

print("\n--- all names ---")
for i, x in enumerate(sorted(r, key=lambda z: z["name"])):
    print(f"  {i+1:>2}. {x['name'][:46]:<48} {x['calories']:>4}cal {x['protein']:>3}p  ctp={x['ctp']}")
