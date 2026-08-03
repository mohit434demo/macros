import fitz, sys, pathlib, unicodedata
SRC = pathlib.Path(r"C:\Users\mohitdhande\OneDrive - Microsoft\Documents\Microsoft Scout\Stealth Health Recipes")
p = list(SRC.glob(sys.argv[1] + "*.pdf"))[0]
doc = fitz.open(p)
print("FILE:", p.name, "pages:", len(doc))
maxp = int(sys.argv[2]) if len(sys.argv) > 2 else 2
for i, page in enumerate(doc):
    if i >= maxp: break
    print(f"===== page {i+1} =====")
    d = page.get_text("dict")
    for blk in d["blocks"]:
        if blk.get("type") != 0: continue
        for line in blk["lines"]:
            for sp in line["spans"]:
                t = unicodedata.normalize("NFKC", sp["text"]).strip()
                if t:
                    print(f"  size={sp['size']:6.2f} y={sp['bbox'][1]:7.1f} x={sp['bbox'][0]:7.1f} | {t[:80]}")
