"""Extract recipes from the Joe x Fitness cookbook -> data/joe_recipes.json

Layout: each recipe starts on a page carrying a "Calories: N" block. The title
is the largest text on that page (24 pt), the macros appear as "Protein: 31g"
style lines, and a "per N ..." caption gives the serving basis. Instructions
live on the following page(s) until the next recipe page, under the heading
"How to make it yourself:".
"""
import fitz, re, json, pathlib, unicodedata

SRC = pathlib.Path(r"C:\Users\mohitdhande\Downloads\Joe x Fitness  COOKBOOK (2).pdf")
OUT = pathlib.Path(__file__).parent.parent / "data"
OUT.mkdir(parents=True, exist_ok=True)

RE_CAL = re.compile(r"Calories:\s*([\d.]+)", re.I)
RE_PRO = re.compile(r"Protein:\s*([\d.]+)\s*g", re.I)
RE_CAR = re.compile(r"Carbs?:\s*([\d.]+)\s*g", re.I)
RE_FAT = re.compile(r"Fat:\s*([\d.]+)\s*g", re.I)
RE_BASIS = re.compile(r"Macros?\s+per\s+([^:]{1,40}):", re.I)
RE_SERV = re.compile(r"\((\d{1,2})\s*servings?\)", re.I)

FOOTER = re.compile(r"^(MACROS MEET UMAMI|\d{1,3})$", re.I)
HEADINGS = re.compile(r"^(How to make it yourself:?|Ingredients?[^:]*:|Macros?\s+per[^:]*:)$", re.I)

# Section titles inside the ingredient column, e.g. "Simple Bulgogi", "Rice"
SECTION_SIZE = 13.5


def clean(s):
    s = unicodedata.normalize("NFKC", s)
    for a, b in [("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2013", "-"), ("\u2014", "-"), ("\u00a0", " ")]:
        s = s.replace(a, b)
    return re.sub(r"[ \t]+", " ", s).strip()


def lines(page):
    out = []
    for blk in page.get_text("dict")["blocks"]:
        if blk.get("type") != 0:
            continue
        for ln in blk["lines"]:
            txt = clean("".join(s["text"] for s in ln["spans"]))
            if not txt:
                continue
            out.append({"t": txt,
                        "size": round(max(s["size"] for s in ln["spans"]), 1),
                        "x": round(ln["bbox"][0], 1), "y": round(ln["bbox"][1], 1)})
    return out


def col_order(ls, width):
    """Ingredient pages use two columns; read left column fully, then right."""
    mid = width / 2
    left = [l for l in ls if l["x"] < mid]
    right = [l for l in ls if l["x"] >= mid]
    if len(left) >= 3 and len(right) >= 3:
        return sorted(left, key=lambda l: l["y"]) + sorted(right, key=lambda l: l["y"])
    return sorted(ls, key=lambda l: (l["y"], l["x"]))


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


doc = fitz.open(SRC)
pages = [lines(p) for p in doc]
texts = ["\n".join(l["t"] for l in p) for p in pages]
widths = [p.rect.width for p in doc]

# section headers ("10 MEAL PREP RECIPES") tell us which category follows.
# Most are 48 pt but the banchan divider is 26.7, so key off a page whose
# largest text is oversized AND which carries no macro block.
CATS = []
for i, ls in enumerate(pages):
    if not ls:
        continue
    top = max(l["size"] for l in ls)
    if top >= 26 and not RE_CAL.search("\n".join(l["t"] for l in ls)):
        big = [l["t"] for l in sorted([x for x in ls if x["size"] >= top - 0.5],
                                      key=lambda l: (l["y"], l["x"]))]
        CATS.append((i, clean(" ".join(big))))

CAT_FIX = {
    "meal prep": "Meal Prep",
    "minute simple meals": "30-Minute",
    "high protein": "High Protein",
    "viral to impress your friends": "Viral",
    "viral": "Viral",
    "korean side dishes aka banchan": "Banchan",
    "korean side dishes": "Banchan",
    "banchan": "Banchan",
    "soups": "Soups",
}

def category_for(idx):
    cur = "Recipes"
    for i, name in CATS:
        if i <= idx:
            cur = name
    n = re.sub(r"^\d+\s*", "", cur.lower())
    n = re.sub(r"\brecipes?\b", "", n)
    n = re.sub(r'["\u201c\u201d]', "", n)
    n = re.sub(r"\s+", " ", n).strip(" -")
    return CAT_FIX.get(n, n.title() or "Recipes")


recipe_pages = [i for i, t in enumerate(texts) if RE_CAL.search(t)]
recipes, problems = [], []

for n, i in enumerate(recipe_pages):
    ls, txt = pages[i], texts[i]
    cal = float(RE_CAL.search(txt).group(1))
    pm, cm, fm = RE_PRO.search(txt), RE_CAR.search(txt), RE_FAT.search(txt)
    if not (pm and fm):
        problems.append((i + 1, "missing protein or fat"))
        continue
    pro, fat = float(pm.group(1)), float(fm.group(1))
    if cm:
        car = float(cm.group(1))
    else:
        # one page omits the carbs line; back it out of the calorie total
        car = max(0, round((cal - pro * 4 - fat * 9) / 4, 1))
        problems.append((i + 1, f"carbs missing, derived {car}g"))
    cal, pro, car, fat = (round(x, 1) for x in (cal, pro, car, fat))

    title_size = max((l["size"] for l in ls if l["size"] >= 18), default=None)
    if not title_size:
        problems.append((i + 1, "no title"))
        continue
    title = clean(" ".join(l["t"] for l in sorted(
        [l for l in ls if l["size"] == title_size], key=lambda l: (l["y"], l["x"]))))
    title = title.title().replace("Bbq", "BBQ").replace("Kbbq", "KBBQ")

    basis_m = RE_BASIS.search(txt)
    basis = clean(basis_m.group(1)) if basis_m else "serving"
    serv_m = RE_SERV.search(txt)
    servings = int(serv_m.group(1)) if serv_m else None

    # blurb = 12 pt text that appears before the macro block
    body = [l for l in ls if 11.5 <= l["size"] <= 12.5 and not FOOTER.match(l["t"])]
    blurb_parts, ingr = [], []
    for l in sorted(body, key=lambda l: (l["y"], l["x"])):
        t = l["t"]
        if re.match(r"^(Protein|Carbs|Fat|Calories):", t, re.I):
            continue
        blurb_parts.append(t)

    # ingredients: everything in the ingredient region, in column order
    ing_head = next((l for l in ls if re.match(r"^Ingredients?", l["t"], re.I)), None)
    if ing_head:
        region = [l for l in ls
                  if l["y"] >= ing_head["y"] - 2 and not FOOTER.match(l["t"])
                  and not HEADINGS.match(l["t"])
                  and not re.match(r"^(Protein|Carbs|Fat|Calories):", l["t"], re.I)]
        for l in col_order(region, widths[i]):
            if l["size"] >= 18:
                continue
            ingr.append(("## " + l["t"]) if l["size"] >= SECTION_SIZE else l["t"])
        blurb_parts = [t for t in blurb_parts
                       if not any(t == x.lstrip("# ") for x in ingr)]

    blurb = " ".join(blurb_parts).strip()

    # steps: sometimes on the recipe page itself, otherwise on the pages after
    # it, stopping at the next recipe or the next section divider (e.g. GUIDES)
    nxt_recipe = recipe_pages[n + 1] if n + 1 < len(recipe_pages) else len(pages)
    nxt_divider = next((c for c, _ in CATS if c > i), len(pages))
    stop = min(nxt_recipe, nxt_divider)

    steps = []
    how = next((l for l in ls if re.match(r"^How to make", l["t"], re.I)), None)
    if how:
        steps += [l["t"] for l in sorted(
            [x for x in ls if x["y"] > how["y"] - 4 and 11 <= x["size"] <= 13
             and not FOOTER.match(x["t"]) and not HEADINGS.match(x["t"])],
            key=lambda l: (l["y"], l["x"]))]
    for j in range(i + 1, stop):
        for l in sorted(pages[j], key=lambda l: (l["y"], l["x"])):
            t = l["t"]
            if FOOTER.match(t) or HEADINGS.match(t) or l["size"] < 11 or l["size"] > 13:
                continue
            steps.append(t)

    # the PDF wraps steps mid-sentence; rejoin so each step is one instruction
    merged = []
    for t in steps:
        if merged and not re.match(r"^[A-Z0-9(\"']", t):
            merged[-1] += " " + t
        elif merged and not re.search(r"[.!?:]$", merged[-1]):
            merged[-1] += " " + t
        else:
            merged.append(t)
    steps = [s for s in merged if len(s) > 12]

    recipes.append({
        "id": "joe-" + slug(title)[:52],
        "name": title,
        "servings": servings,
        "basis": basis,
        "calories": cal, "protein": pro, "carbs": car, "fat": fat,
        "ctp": round(cal / pro, 1) if pro else None,
        "category": category_for(i),
        "blurb": blurb,
        "ingredients": ingr,
        "steps": steps,
        "page": i + 1,
    })

doc.close()

seen = set()
for r in recipes:
    base, k = r["id"], 2
    while r["id"] in seen:
        r["id"] = f"{base}-{k}"; k += 1
    seen.add(r["id"])

(OUT / "joe_recipes.json").write_text(json.dumps(recipes, indent=1, ensure_ascii=False),
                                      encoding="utf-8")

print(f"recipe pages : {len(recipe_pages)}")
print(f"recipes      : {len(recipes)}")
print(f"with steps   : {sum(1 for r in recipes if r['steps'])}")
print(f"with ingr    : {sum(1 for r in recipes if r['ingredients'])}")
print(f"with blurb   : {sum(1 for r in recipes if r['blurb'])}")
print(f"problems     : {len(problems)}")
for p in problems:
    print("   page", p[0], "->", p[1])
cats = {}
for r in recipes:
    cats[r["category"]] = cats.get(r["category"], 0) + 1
print("categories   :", cats)
