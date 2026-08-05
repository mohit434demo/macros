import json, pathlib, re

ROOT = pathlib.Path(__file__).parent.parent
st = json.loads((ROOT / "data/recipes.json").read_text(encoding="utf-8"))
jo = json.loads((ROOT / "data/joe_recipes.json").read_text(encoding="utf-8"))
js = (ROOT / "site/pantrymatch.js").read_text(encoding="utf-8")
items = json.loads(re.search(r"PANTRY_ITEMS = (\[.*?\]);", js, re.S).group(1))
needs = json.loads(re.search(r"RECIPE_NEEDS = (\{.*?\});", js, re.S).group(1))
staple = {i["id"] for i in items if i["s"]}
by = {r["id"]: r for r in st + jo}

zero = [k for k, v in needs.items() if not [x for x in v if x not in staple]]
print("zero non-staple needs:", len(zero))
for k in zero:
    r = by[k]
    print(f"  {r['name'][:42]:<44} ingr={len(r['ingredients']):>2} needs={needs[k]}")
    for i in r["ingredients"][:4]:
        print(f"        {i[:66]}")

print("\n--- distribution of non-staple needs ---")
import collections
d = collections.Counter(len([x for x in v if x not in staple]) for v in needs.values())
for k in sorted(d):
    print(f"  {k:>2} needs : {d[k]:>3} recipes")
