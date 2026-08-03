"""How many of the 70 extracted recipes can get a PDF link and/or a video link?"""
import fitz, json, pathlib

SRC = pathlib.Path(r"C:\Users\mohitdhande\OneDrive - Microsoft\Documents\Microsoft Scout\Stealth Health Recipes")
ROOT = pathlib.Path(__file__).parent.parent
recipes = json.loads((ROOT / "data/recipes.json").read_text(encoding="utf-8"))
idx = {e["file"]: e for e in json.loads((SRC / "index.json").read_text(encoding="utf-8"))}

vids = {}
for pdf in sorted(SRC.glob("*.pdf")):
    doc = fitz.open(pdf)
    for page in doc:
        for l in page.get_links():
            u = l.get("uri")
            if u and "instagram" in u:
                vids.setdefault(pdf.name, u)
    doc.close()

has_pdf = has_vid = neither = 0
missing = []
for r in recipes:
    p = r["source"] in idx
    v = r["source"] in vids
    has_pdf += p
    has_vid += v
    if not p:
        missing.append((r["name"], r["source"]))
    if not p and not v:
        neither += 1

print(f"recipes            : {len(recipes)}")
print(f"with PDF link      : {has_pdf}")
print(f"with video link    : {has_vid}")
print(f"with neither       : {neither}")
print("\nno PDF url:")
for n, s in missing:
    print(f"   {n[:44]:<46} {s[:48]}")
