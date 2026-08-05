"""How much step prose leaked into ingredient lists?"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).parent.parent
stealth = json.loads((ROOT / "data/recipes.json").read_text(encoding="utf-8"))
joe = json.loads((ROOT / "data/joe_recipes.json").read_text(encoding="utf-8"))

VERBS = re.compile(r"\b(add|stir|cook|serve|store|reheat|mix|divide|transfer|let|"
                   r"place|remove|repeat|enjoy|shred|pour|heat|bake|top|make|"
                   r"leftovers|microwave|freezer|ensure|prefer|important|"
                   r"before|after|during|until|while)\b", re.I)


def looks_like_prose(s):
    if s.startswith("## "):
        return False
    words = s.split()
    if len(words) >= 9 and VERBS.search(s):
        return True
    if len(s) > 85:
        return True
    return False


for label, book in (("Stealth Health", stealth), ("Joe x Fitness", joe)):
    bad_lines = 0
    total = 0
    bad_recipes = []
    for r in book:
        ing = [i for i in r["ingredients"]]
        total += len(ing)
        n = sum(1 for i in ing if looks_like_prose(i))
        bad_lines += n
        if n:
            bad_recipes.append((r["name"], n, len(ing)))
    print(f"=== {label} ===")
    print(f"  ingredient lines: {total}   prose-looking: {bad_lines} "
          f"({100*bad_lines//max(1,total)}%)")
    print(f"  recipes affected: {len(bad_recipes)} of {len(book)}")
    for n, b, t in sorted(bad_recipes, key=lambda x: -x[1])[:8]:
        print(f"     {n[:44]:<46} {b}/{t}")
    print()

print("--- worst offenders (samples) ---")
for r in stealth + joe:
    for i in r["ingredients"]:
        if looks_like_prose(i):
            print(f"  [{r['name'][:26]:<28}] {i[:96]}")
            break
