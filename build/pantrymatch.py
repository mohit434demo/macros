"""Map free-text recipe ingredients to canonical pantry items.

Emits site/pantrymatch.js containing:
  PANTRY_ITEMS  - the checklist the user ticks (grouped, with staples flagged)
  RECIPE_NEEDS  - recipeId -> [pantry item ids] it requires

Matching is deliberately generous: "chicken" covers breast and thighs, "onion"
covers yellow/red/white. A false "you can make this" is a minor annoyance; a
false "you cannot" hides a recipe you could have cooked.
"""
import json, re, pathlib, collections

ROOT = pathlib.Path(__file__).parent.parent

# ---------------------------------------------------------------- catalogue
# (id, label, group, staple?, regex)  -- first match wins, so order matters
ITEMS = [
    # ---- assumed staples: seasonings, oils, basic pantry
    ("salt",        "Salt",              "Seasonings", 1, r"\bsalt\b"),
    ("pepper",      "Black pepper",      "Seasonings", 1, r"\b(black )?pepper\b(?!.*\b(bell|red pepper flake|chili)\b)"),
    ("oil",         "Cooking oil",       "Seasonings", 1, r"\b(spray oil|avocado oil|olive oil|vegetable oil|canola|cooking oil|neutral oil|^oil$)"),
    ("water",       "Water",             "Seasonings", 1, r"\bwater\b"),
    ("sugar",       "Sugar",             "Seasonings", 1, r"\b(brown sugar|white sugar|granulated|sugar)\b"),
    ("flour",       "Flour",             "Seasonings", 1, r"\b(all.purpose flour|flour)\b"),
    ("cornstarch",  "Cornstarch",        "Seasonings", 1, r"\bcorn ?starch\b"),
    ("bakingsoda",  "Baking soda/powder","Seasonings", 1, r"\bbaking (soda|powder)\b"),
    ("vinegar",     "Vinegar",           "Seasonings", 1, r"\bvinegar\b"),
    ("garlicpwd",   "Garlic powder",     "Seasonings", 1, r"\bgarlic powder\b"),
    ("onionpwd",    "Onion powder",      "Seasonings", 1, r"\bonion powder\b"),
    ("paprika",     "Paprika",           "Seasonings", 1, r"\bpaprika\b"),
    ("cumin",       "Cumin",             "Seasonings", 1, r"\bcumin\b"),
    ("chilipwd",    "Chili powder",      "Seasonings", 1, r"\b(chili|chile|ancho|cayenne|curry) powder\b|\bcayenne\b"),
    ("italian",     "Italian seasoning", "Seasonings", 1, r"\b(italian seasoning|oregano|basil|thyme|rosemary)\b"),
    ("sesameseed",  "Sesame seeds",      "Seasonings", 1, r"\bsesame seeds?\b"),
    ("sesameoil",   "Sesame oil",        "Seasonings", 1, r"\bsesame oil\b"),
    ("soy",         "Soy sauce",         "Seasonings", 1, r"\b(soy sauce|tamari|coconut aminos)\b"),
    ("honey",       "Honey",             "Seasonings", 1, r"\b(honey|agave|maple syrup)\b"),
    ("garlic",      "Garlic",            "Seasonings", 1, r"\bgarlic\b(?! powder)"),
    ("ginger",      "Ginger",            "Seasonings", 1, r"\bginger\b"),
    ("stock",       "Broth or stock",    "Seasonings", 1, r"\b(broth|stock|bouillon)\b"),
    ("tacoseason",  "Taco seasoning",    "Seasonings", 1, r"\b(taco seasoning|fajita seasoning|ranch seasoning|everything bagel)\b"),
    ("bayleaf",     "Bay leaves",        "Seasonings", 1, r"\bbay leaf|bay leaves\b"),
    ("mustard",     "Mustard",           "Seasonings", 1, r"\b(dijon|mustard)\b"),
    ("mirin",       "Mirin or rice wine","Seasonings", 1, r"\b(mirin|rice wine|cooking wine|sake)\b"),

    # ---- proteins
    ("chicken",     "Chicken",           "Protein", 0, r"\bchicken\b(?!.*\b(broth|stock|bouillon|powder)\b)"),
    ("beef",        "Beef or steak",     "Protein", 0, r"\b(ground beef|beef|steak|ribeye|sirloin|flank|brisket|bulgogi meat|chuck)\b(?!.*\b(broth|stock|bouillon)\b)"),
    ("pork",        "Pork",              "Protein", 0, r"\b(pork|bacon|sausage|ham|chorizo|prosciutto)\b"),
    ("turkey",      "Ground turkey",     "Protein", 0, r"\bturkey\b"),
    ("shrimp",      "Shrimp",            "Protein", 0, r"\b(shrimp|prawns?)\b"),
    ("salmon",      "Salmon",            "Protein", 0, r"\b(salmon|lox)\b"),
    ("tuna",        "Tuna",              "Protein", 0, r"\btuna\b"),
    ("fish",        "Other fish",        "Protein", 0, r"\b(tilapia|cod|white fish|anchov|fish cake|eomuk|squid|ojingeo)\b"),
    ("eggs",        "Eggs",              "Protein", 0, r"\begg\b|\beggs\b"),
    ("tofu",        "Tofu",              "Protein", 0, r"\b(tofu|soondubu)\b"),
    ("deli",        "Deli meat",         "Protein", 0, r"\bdeli\b"),

    # ---- dairy
    ("greekyog",    "Greek yogurt",      "Dairy", 0, r"\b(greek yogurt|skyr|yogurt)\b"),
    ("cottage",     "Cottage cheese",    "Dairy", 0, r"\bcottage cheese\b"),
    ("creamcheese", "Cream cheese",      "Dairy", 0, r"\bcream cheese\b"),
    ("cheddar",     "Cheddar",           "Dairy", 0, r"\bcheddar\b"),
    ("mozz",        "Mozzarella",        "Dairy", 0, r"\bmozzarella\b"),
    ("parm",        "Parmesan",          "Dairy", 0, r"\b(parmesan|parmigiano|pecorino)\b"),
    ("jack",        "Jack or queso",     "Dairy", 0, r"\b(monterey jack|pepper jack|queso|oaxaca|american cheese|velveeta)\b"),
    ("feta",        "Feta",              "Dairy", 0, r"\b(feta|cotija)\b"),
    ("butter",      "Butter",            "Dairy", 0, r"\bbutter\b(?!.*\b(peanut|almond|chicken)\b)"),
    ("milk",        "Milk",              "Dairy", 0, r"\bmilk\b(?!.*coconut)"),
    ("cheeseother", "Other cheese",      "Dairy", 0, r"\b(cheese|ricotta)\b"),

    # ---- carbs
    ("rice",        "Rice",              "Carbs", 0, r"\brice\b(?!.*\b(vinegar|paper|cake|wine)\b)"),
    ("pasta",       "Pasta",             "Carbs", 0, r"\b(pasta|ziti|penne|shells|macaroni|spaghetti|lasagna noodle|rigatoni)\b"),
    ("noodles",     "Asian noodles",     "Carbs", 0, r"\b(udon|ramen|glass noodle|sweet potato noodle|japchae|dangmyeon|vermicelli|rice noodle)\b"),
    ("ricepaper",   "Rice paper",        "Carbs", 0, r"\brice paper\b"),
    ("tortilla",    "Tortillas",         "Carbs", 0, r"\b(tortillas?|wraps?)\b"),
    ("bread",       "Bread or buns",     "Carbs", 0, r"\b(bread|bun|english muffin|bagel|sourdough|brioche)\b"),
    ("potato",      "Potatoes",          "Carbs", 0, r"\b(potato|potatoes|fries|tots)\b"),
    ("beans",       "Beans or lentils",  "Carbs", 0, r"\b(black beans?|pinto|refried|chickpeas?|lentils?|kidney beans?|beans?)\b"),
    ("ricecake",    "Rice cakes",        "Carbs", 0, r"\b(rice cake|tteok|dduk)\b"),
    ("oats",        "Oats",              "Carbs", 0, r"\boats?\b"),
    ("panko",       "Panko or breadcrumb","Carbs", 0, r"\b(panko|bread ?crumb)\b"),

    # ---- produce
    ("onion",       "Onion",             "Produce", 0, r"\bonions?\b(?! powder)(?!.*\bgreen\b)"),
    ("greenonion",  "Green onion",       "Produce", 0, r"\b(green onions?|scallions?|spring onions?|chives?)\b"),
    ("cilantro",    "Cilantro",          "Produce", 0, r"\bcilantro\b"),
    ("bellpepper",  "Bell pepper",       "Produce", 0, r"\b(bell peppers?|poblano)\b"),
    ("chilipepper", "Chili pepper",      "Produce", 0, r"\b(jalapenos?|serranos?|chipotles?|gochugaru|red pepper flakes?|dried chiles?|guajillo|habanero|green chiles?|chili oil)\b"),
    ("cucumber",    "Cucumber",          "Produce", 0, r"\bcucumbers?\b"),
    ("lettuce",     "Lettuce",           "Produce", 0, r"\b(lettuce|salad green|romaine)\b"),
    ("cabbage",     "Cabbage",           "Produce", 0, r"\b(cabbage|coleslaw|napa)\b"),
    ("carrot",      "Carrot",            "Produce", 0, r"\bcarrots?\b"),
    ("broccoli",    "Broccoli",          "Produce", 0, r"\bbroccoli\b"),
    ("spinach",     "Spinach",           "Produce", 0, r"\b(spinach|sigeumchi)\b"),
    ("mushroom",    "Mushrooms",         "Produce", 0, r"\b(mushrooms?|enoki|shiitake)\b"),
    ("tomato",      "Tomatoes",          "Produce", 0, r"\btomato(es)?\b(?! paste)"),
    ("avocado",     "Avocado",           "Produce", 0, r"\bavocado\b(?! oil)"),
    ("lime",        "Lime or lemon",     "Produce", 0, r"\b(lime|lemon)\b"),
    ("zucchini",    "Zucchini or squash","Produce", 0, r"\b(zucchini|squash)\b"),
    ("corn",        "Corn",              "Produce", 0, r"\bcorn\b(?!.*\b(starch|tortilla|syrup)\b)"),
    ("radish",      "Radish",            "Produce", 0, r"\b(radish|daikon|mu\b)"),
    ("pineapple",   "Pineapple",         "Produce", 0, r"\bpineapple\b"),
    ("seaweed",     "Seaweed",           "Produce", 0, r"\b(seaweed|gim|nori|miyeok)\b"),

    # ---- sauces and pastes
    ("gochujang",   "Gochujang",         "Sauces", 0, r"\bgochujang\b"),
    ("kimchi",      "Kimchi",            "Sauces", 0, r"\bkimchi\b"),
    ("tomatopaste", "Tomato paste",      "Sauces", 0, r"\btomato paste\b"),
    ("salsa",       "Salsa or enchilada","Sauces", 0, r"\b(salsa|enchilada sauce|pico de gallo|adobo|taco sauce)\b"),
    ("hotsauce",    "Hot sauce",         "Sauces", 0, r"\b(sriracha|hot sauce|buffalo sauce|chili crisp|chili garlic|sambal|gochujang paste)\b"),
    ("mayo",        "Mayo",              "Sauces", 0, r"\bmayo|mayonnaise\b"),
    ("bbq",         "BBQ sauce",         "Sauces", 0, r"\bbbq sauce|barbecue\b"),
    ("oyster",      "Oyster or fish sauce","Sauces", 0, r"\b(oyster sauce|fish sauce|ponzu|hoisin|teriyaki)\b"),
    ("miso",        "Miso",              "Sauces", 0, r"\bmiso\b"),
    ("peanutbutter","Peanut butter",     "Sauces", 0, r"\b(peanut butter|almond butter|tahini)\b"),
    ("pesto",       "Pesto or alfredo",  "Sauces", 0, r"\b(pesto|alfredo sauce|vodka sauce|marinara)\b"),
    ("nutritional", "Nutritional yeast", "Sauces", 0, r"\bnutritional yeast\b"),
]

COMPILED = [(i, lbl, grp, bool(st), re.compile(rx, re.I)) for i, lbl, grp, st, rx in ITEMS]
BY_ID = {i: (lbl, grp, bool(st)) for i, lbl, grp, st, _ in ITEMS}


def canon(line):
    """Every pantry item mentioned in one ingredient line."""
    s = re.sub(r"\([^)]*\)", " ", line.lower())
    s = re.sub(r"\s+", " ", s)
    hits = []
    for iid, _lbl, _grp, _st, rx in COMPILED:
        if rx.search(s):
            hits.append(iid)
    return hits


stealth = json.loads((ROOT / "data/recipes.json").read_text(encoding="utf-8"))
joe = json.loads((ROOT / "data/joe_recipes.json").read_text(encoding="utf-8"))

needs = {}
skipped = []
unmatched = collections.Counter()
for r in stealth + joe:
    ids = set()
    real_lines = 0
    for line in r["ingredients"]:
        if line.startswith("## ") or line.rstrip().endswith(":"):
            continue
        real_lines += 1
        got = canon(line)
        if got:
            ids.update(got)
        elif len(line) > 3:
            unmatched[line.lower()[:48]] += 1
    # A few PDFs have unusable ingredient blocks. Claiming "you can make this"
    # from three lines of leftover text would be worse than saying nothing, so
    # exclude them from matching instead of guessing.
    if real_lines < 4:
        skipped.append(r["name"])
        continue
    needs[r["id"]] = sorted(ids)

items = [{"id": i, "n": lbl, "g": grp, "s": 1 if st else 0}
         for i, lbl, grp, st, _ in ITEMS]

js = "// Generated by build/pantrymatch.py - do not edit by hand.\n"
js += "const PANTRY_ITEMS = " + json.dumps(items, separators=(",", ":")) + ";\n"
js += "const RECIPE_NEEDS = " + json.dumps(needs, separators=(",", ":")) + ";\n"
(ROOT / "site" / "pantrymatch.js").write_text(js, encoding="utf-8")

nonstaple = [len([x for x in v if not BY_ID[x][2]]) for v in needs.values()]
nonstaple.sort()
print(f"recipes mapped     : {len(needs)}")
print(f"excluded (thin data): {len(skipped)}")
for s in skipped:
    print(f"     {s[:52]}")
print(f"pantry items       : {len(items)} ({sum(1 for i in items if i['s'])} staples)")
print(f"non-staple needs   : min={nonstaple[0]} median={nonstaple[len(nonstaple)//2]} max={nonstaple[-1]}")
print(f"recipes with 0 needs: {sum(1 for n in nonstaple if n == 0)}")
print(f"unmatched lines    : {sum(unmatched.values())}")
print(f"wrote site/pantrymatch.js ({len(js)/1024:.1f} KB)")
print("\n--- top unmatched (candidates for the catalogue) ---")
for k, v in unmatched.most_common(25):
    print(f"  {v:>3}  {k}")
