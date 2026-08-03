import json, pathlib
r = json.loads((pathlib.Path(__file__).parent.parent / "data/recipes.json").read_text(encoding="utf-8"))
print("--- sample ---")
for x in r[:30]:
    print(f"{x['name'][:44]:<46} {x['calories']:>4}cal {x['protein']:>3}p {x['carbs']:>3}c {x['fat']:>3}f  sv={x['servings']} ing={len(x['ingredients'])} st={len(x['steps'])}")
print("\n--- recipes with NO steps:", sum(1 for x in r if not x["steps"]), "---")
for x in r:
    if not x["steps"]:
        print("  ", x["name"][:48], "|", x["source"][:46])
print("\n--- suspicious names (look like filenames/subjects) ---")
for x in r:
    if any(k in x["name"].lower() for k in ["mpw", "recipe", "detailed", "free ", "new ", "!", "+"]):
        print("  ", x["name"][:60], "|", x["source"][:40])
