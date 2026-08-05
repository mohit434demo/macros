"""Extract recipes from Stealth Health / Meal Prep Weekly PDFs -> data/recipes.json

Layout notes learned from the source PDFs:
  * Recipe title is always the largest font on its page; macro callouts are the
    next size down and match the macro regexes, so they are filtered out.
  * Step numbers appear either as an inline prefix ("1. Dice the onion") or as a
    standalone marker line *after* the step text, depending on the template.
  * A few files are multi-recipe cookbooks with one recipe per page.
"""
import fitz, re, json, pathlib, unicodedata

SRC = pathlib.Path(r"C:\Users\mohitdhande\OneDrive - Microsoft\Documents\Microsoft Scout\Stealth Health Recipes")
OUT = pathlib.Path(__file__).parent.parent / "data"
OUT.mkdir(parents=True, exist_ok=True)

RE_CAL = re.compile(r"(\d{2,4})\s*Calories", re.I)
RE_PRO = re.compile(r"(\d{1,3})\s*G\s*Protein", re.I)
RE_CAR = re.compile(r"(\d{1,3})\s*G\s*Carbs", re.I)
RE_FAT = re.compile(r"(\d{1,3})\s*G\s*Fat", re.I)
RE_SERV = re.compile(r"makes\s*[:\s]*(\d{1,3})", re.I)
RE_MACROISH = re.compile(r"\d+\s*(Calories|G\s*(Protein|Carbs|Fat))", re.I)
RE_MARKER = re.compile(r"^\d{1,2}\s*[.)]?$")
# "1.Dice the onion" often has no space after the period; the letter lookahead
# keeps quantities like "1.5 cups" from being mistaken for a step marker.
RE_INLINE = re.compile(r"^\s*(\d{1,2})\s*[.)]\s*(?=[A-Za-z])")

NOISE = re.compile(
    r"^(ingredients?|instructions?|directions?|toppings?|per serving.*|grocery list.*|"
    r"watch recipe video|instructions begin on next page|use while shopping|"
    r"ingredient list.*|per .{0,20}: ?makes.*|additional recipe notes.*|"
    r"back to table of contents.*|tom walsh|meals|\(meal prep weekly.*\)|"
    r"stealth health|slow cooker cookbook|\d+)\s*$", re.I)

SECTION_HDR = re.compile(r"^[A-Z][A-Za-z0-9%'&/ -]{1,30}:\s*$")


def clean(s):
    s = unicodedata.normalize("NFKC", s)
    for a, b in [("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2013", "-"), ("\u2014", "-"), ("\u00a0", " "), ("\ufb01", "fi")]:
        s = s.replace(a, b)
    return re.sub(r"[ \t]+", " ", s).strip()


def spans(page):
    out = []
    for blk in page.get_text("dict")["blocks"]:
        if blk.get("type") != 0:
            continue
        for line in blk["lines"]:
            txt = clean("".join(sp["text"] for sp in line["spans"]))
            if txt:
                size = max(sp["size"] for sp in line["spans"])
                out.append({"t": txt, "size": round(size, 2),
                            "y": line["bbox"][1], "x": line["bbox"][0]})
    return out


def page_title(sp_list):
    """Largest-font text on the page, excluding macro callouts and boilerplate."""
    cands = [s for s in sp_list
             if not RE_MACROISH.search(s["t"]) and not NOISE.match(s["t"])
             and len(s["t"]) > 2 and not SECTION_HDR.match(s["t"])]
    if not cands:
        return None
    top = max(s["size"] for s in cands)
    picked = [s for s in cands if s["size"] >= top - 0.6]
    picked.sort(key=lambda s: (round(s["y"] / 8), s["x"]))
    title = " ".join(s["t"] for s in picked)
    title = re.sub(r"\s+", " ", title).strip(" -:")
    if len(title) > 70 or len(title) < 3:
        return None
    return title


def reading_order(sp_list, width):
    mid = width / 2
    left = [s for s in sp_list if s["x"] < mid]
    right = [s for s in sp_list if s["x"] >= mid]
    if len(left) >= 3 and len(right) >= 3:
        return sorted(left, key=lambda s: s["y"]) + sorted(right, key=lambda s: s["y"])
    return sorted(sp_list, key=lambda s: (s["y"], s["x"]))


def macros(text):
    def one(rx):
        m = rx.search(text)
        return int(m.group(1)) if m else None
    return one(RE_CAL), one(RE_PRO), one(RE_CAR), one(RE_FAT)


def macro_groups(sp_list):
    """Group macro callouts by vertical position.

    Some pages carry two labelled sets, e.g. "Per BURRITO BOWL (makes 10)" at
    595 cal alongside "CARNE ASADA ONLY (PER 4OZ, MAKES 16)" at 195 cal. Each
    set sits on its own row, so cluster by y and keep only complete sets.
    """
    labels = []
    for s in sp_list:
        m = RE_SERV.search(s["t"])
        if m:
            labels.append((s["y"], int(m.group(1))))

    rows = {}
    for s in sp_list:
        for key, rx in (("calories", RE_CAL), ("protein", RE_PRO),
                        ("carbs", RE_CAR), ("fat", RE_FAT)):
            m = rx.search(s["t"])
            if m:
                rows.setdefault(round(s["y"] / 6), {})[key] = int(m.group(1))

    groups = []
    for yk, d in rows.items():
        if len(d) == 4:
            y = yk * 6
            above = [(y - ly, n) for ly, n in labels if ly <= y + 6]
            d["servings"] = min(above)[1] if above else None
            groups.append(d)
    return groups


RE_QTY = re.compile(
    r"(^\s*[\d\u00bc-\u00be\u2150-\u215e]|"                      # starts with a number/fraction
    r"\b\d+\s*(g|kg|oz|lb|lbs|ml|l)\b|"                          # 400g, 14oz
    r"\b(tbsp|tsp|tablespoons?|teaspoons?|cups?|cloves?|cans?|"
    r"jars?|packages?|bunch(es)?|slices?|handful|dash|pinch|"
    r"sprigs?|heads?|stalks?|leaves|sheets?|scoops?|sticks?)\b)", re.I)

RE_PROSE = re.compile(
    r"\b(add|stir|cook|serve|store|reheat|mix|divide|transfer|place|remove|repeat|"
    r"enjoy|shred|pour|heat|bake|microwave|freeze|cool|wrap|garnish|top it|let the|"
    r"leftovers|until|before|after|during|so that|make sure|be sure|note:|tip:|"
    r"you can|if you|this is|which|resulting)\b", re.I)


def is_ingredient(line):
    """Ingredient lines are short and quantity-led; trailing storage and
    reheating notes are full sentences. Keep them apart so the ingredient
    list stays usable for pantry matching."""
    t = line.strip()
    if not t:
        return False
    if SECTION_HDR.match(t) or t.endswith(":"):
        return True
    words = t.split()
    has_qty = bool(RE_QTY.search(t))
    # sentence fragments left over from wrapped prose ("containers.", "eat.")
    if t.endswith(".") and not has_qty and not re.search(r"\d", t):
        return False
    if has_qty and len(words) <= 16 and not (len(words) > 9 and RE_PROSE.search(t)):
        return True
    if len(words) <= 6 and not RE_PROSE.search(t) and len(t) >= 4:
        return True
    return False


def parse_body(lines):
    """Split lines into (ingredients, steps), handling both numbering styles."""
    lines = [l for l in lines if not NOISE.match(l) and not RE_MACROISH.search(l)]
    standalone = sum(1 for l in lines if RE_MARKER.match(l))
    inline = sum(1 for l in lines if RE_INLINE.match(l))
    steps, ingr = [], []

    if standalone >= 2 and standalone >= inline:
        buf = []
        for l in lines:
            if RE_MARKER.match(l):
                if buf:
                    steps.append(" ".join(buf))
                    buf = []
            else:
                buf.append(l)
        # everything after the final marker: ingredients plus trailing notes
        tail_ingr, tail_prose = [], []
        for l in buf:
            (tail_ingr if is_ingredient(l) else tail_prose).append(l)
        ingr = tail_ingr
        if tail_prose and steps:
            steps[-1] = steps[-1].rstrip() + " " + " ".join(tail_prose)
        elif tail_prose:
            steps.append(" ".join(tail_prose))
        if steps:
            first = steps[0]
            m = re.search(r"(?:^|\s)((?:Add|Dice|Cook|Preheat|In a|Combine|Mix|Heat|Place|"
                          r"Bring|Season|Transfer|Stir|Chop|Slice|Brown|Boil|Whisk|Spray|Line)\b)", first)
            if m and m.start(1) > 0:
                ingr = [first[:m.start(1)].strip()] + ingr
                steps[0] = first[m.start(1):].strip()
    else:
        buf = None
        for l in lines:
            if RE_INLINE.match(l):
                if buf:
                    steps.append(buf)
                buf = RE_INLINE.sub("", l).strip()
            elif buf is not None:
                buf += " " + l
            else:
                ingr.append(l)
        if buf:
            steps.append(buf)

    ingr = [i for i in ingr if 2 < len(i) < 120 and is_ingredient(i)]
    steps = [s for s in steps if len(s) > 15]
    return ingr, steps


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


index = {}
p = SRC / "index.json"
if p.exists():
    for e in json.loads(p.read_text(encoding="utf-8")):
        index[e["file"]] = e

raw, problems = [], []

for pdf in sorted(SRC.glob("*.pdf")):
    meta = index.get(pdf.name, {})
    try:
        doc = fitz.open(pdf)
    except Exception as ex:
        problems.append((pdf.name, f"open failed: {ex}"))
        continue

    pages = []
    video = None
    for pg in doc:
        sp = spans(pg)
        pages.append({"spans": sp, "w": pg.rect.width,
                      "text": "\n".join(s["t"] for s in sp)})
        # "Watch recipe video" is an annotation, not text; only some editions have one
        for lnk in pg.get_links():
            uri = lnk.get("uri") or ""
            if "instagram.com" in uri or "youtu" in uri or "tiktok" in uri:
                video = video or uri
    doc.close()
    if not pages:
        problems.append((pdf.name, "no text"))
        continue

    whole = "\n".join(pg["text"] for pg in pages)
    doc_title = page_title(pages[0]["spans"])
    subject = clean(meta.get("subject") or pdf.stem.replace("_", " "))
    subject = re.sub(r"\s*[+&]\s*(meal prep containers|book update|free|new).*$", "", subject, flags=re.I)
    subject = re.sub(r"^(ICYMI:|Free|New)\s*", "", subject, flags=re.I).strip()

    rec_pages = []
    for i, pg in enumerate(pages):
        if re.search(r"grocery list", pg["text"], re.I):
            continue
        t = macros(pg["text"])
        # "makes N" covers "Per SERVING: makes 10" and "Per Burrito: Makes 15"
        if all(v is not None for v in t) and RE_SERV.search(pg["text"]):
            rec_pages.append(i)

    if not rec_pages:
        t = macros(whole)
        if not all(v is not None for v in t):
            problems.append((pdf.name, "no macros"))
            continue
        sm = RE_SERV.search(whole)
        raw.append({"name": doc_title or subject, "servings": int(sm.group(1)) if sm else None,
                    "calories": t[0], "protein": t[1], "carbs": t[2], "fat": t[3],
                    "ingredients": [], "steps": [], "source": pdf.name,
                    "video": video, "meta": meta})
        continue

    multi = len(rec_pages) > 1
    for i in rec_pages:
        pg = pages[i]
        groups = macro_groups(pg["spans"])
        sm = RE_SERV.search(pg["text"]) or RE_SERV.search(whole)
        servings = int(sm.group(1)) if sm else None
        if len(groups) > 1:
            # prefer the assembled meal over a single component
            g = max(groups, key=lambda d: d["calories"])
            cal, pro, car, fat = g["calories"], g["protein"], g["carbs"], g["fat"]
            servings = g.get("servings") or servings
        else:
            cal, pro, car, fat = macros(pg["text"])

        body_spans = list(pg["spans"])
        for j in (i + 1, i + 2):
            if j >= len(pages):
                break
            nxt = pages[j]
            if re.search(r"grocery list", nxt["text"], re.I) or RE_SERV.search(nxt["text"]):
                break
            if re.search(r"instructions|ingredient list", nxt["text"], re.I):
                body_spans += nxt["spans"]
        lines = [s["t"] for s in reading_order(body_spans, pg["w"])]
        ingr, steps = parse_body(lines)

        if not ingr:
            # Dense "print" layouts interleave ingredients with recipe notes, so the
            # column walk hands them to the step buffer. Recover quantity-led lines
            # that are not already part of a step.
            joined = " ".join(steps)
            seen_i = set()
            for l in lines:
                if NOISE.match(l) or RE_MACROISH.search(l) or RE_MARKER.match(l):
                    continue
                if not RE_QTY.search(l) or not is_ingredient(l):
                    continue
                if l in joined or l.lower() in seen_i:
                    continue
                seen_i.add(l.lower())
                ingr.append(l)

        if len([x for x in ingr if not x.rstrip().endswith(":")]) < 4:
            # Most of these PDFs also carry a "Grocery list - use while shopping"
            # page: a clean, categorised ingredient list. It is the better source
            # whenever the recipe page itself did not yield much.
            for gp in pages:
                if not re.search(r"grocery list", gp["text"], re.I):
                    continue
                got = []
                for s in reading_order(gp["spans"], gp["w"]):
                    t = s["t"]
                    if NOISE.match(t) or RE_MACROISH.search(t) or RE_SERV.search(t):
                        continue
                    if s["size"] >= 18 or len(t) < 3:
                        continue
                    got.append(t)
                if len(got) > len(ingr):
                    ingr = got
                break

        title = (page_title(pg["spans"]) if multi else doc_title) or subject
        if RE_MACROISH.search(title or ""):
            title = subject
        raw.append({"name": title, "servings": servings,
                    "calories": cal, "protein": pro, "carbs": car, "fat": fat,
                    "ingredients": ingr, "steps": steps,
                    "source": pdf.name, "video": video, "meta": meta})

# ---- de-duplicate: same macros + servings == same dish across template variants.
# Variants differ in quality: the "recipe card" usually has clean ingredients while
# the "detailed"/"print" version has better steps. Take the best of each.
best = {}
for r in raw:
    key = (r["calories"], r["protein"], r["carbs"], r["fat"], r["servings"])
    prev = best.get(key)
    if prev is None:
        best[key] = r
        continue
    keep = prev
    if len(r["steps"]) > len(keep["steps"]):
        keep = dict(keep, steps=r["steps"])
    if len(r["ingredients"]) > len(keep["ingredients"]):
        keep = dict(keep, ingredients=r["ingredients"])
    if len(r["name"]) > len(keep["name"]):
        keep = dict(keep, name=r["name"])
    keep["video"] = keep.get("video") or r.get("video")
    if not keep.get("meta", {}).get("url") and r.get("meta", {}).get("url"):
        keep["meta"] = r["meta"]
    best[key] = keep

recipes = []
for r in best.values():
    m = r.pop("meta", {})
    name = re.sub(r"\s+", " ", r["name"]).strip().title()
    name = name.replace("Bbq", "BBQ").replace("Mpw", "").replace(" N ", " N' ")
    name = re.sub(r"\s+", " ", name).strip(" -:")
    r["name"] = name
    r["id"] = slug(name)[:60]
    # drop headings that survived as ingredient lines (the dish title, serving
    # captions) so the list is purely things you would shop for
    low = name.lower()
    r["ingredients"] = [
        i for i in r["ingredients"]
        if i.lower().strip(" :") != low
        and not RE_SERV.search(i)
        and not NOISE.match(i)
        and not RE_MACROISH.search(i)
    ]
    r["edition"] = m.get("edition")
    r["date"] = m.get("date")
    r["pdf"] = m.get("url")
    r["ctp"] = round(r["calories"] / r["protein"], 1) if r["protein"] else None
    recipes.append(r)

seen = set()
for r in recipes:
    base, n = r["id"], 2
    while r["id"] in seen:
        r["id"] = f"{base}-{n}"; n += 1
    seen.add(r["id"])

recipes.sort(key=lambda r: r["name"])
(OUT / "recipes.json").write_text(json.dumps(recipes, indent=1, ensure_ascii=False), encoding="utf-8")

print(f"PDFs         : {len(list(SRC.glob('*.pdf')))}")
print(f"Recipes      : {len(recipes)}")
print(f"With steps   : {sum(1 for r in recipes if r['steps'])}")
print(f"With ingr    : {sum(1 for r in recipes if r['ingredients'])}")
print(f"With servings: {sum(1 for r in recipes if r['servings'])}")
print(f"With PDF url : {sum(1 for r in recipes if r.get('pdf'))}")
print(f"With video   : {sum(1 for r in recipes if r.get('video'))}")
print(f"Problems     : {len(problems)}")
for x in problems:
    print("   ", x[0], "->", x[1])
