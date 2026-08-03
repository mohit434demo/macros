import fitz, sys, pathlib

SRC = pathlib.Path(r"C:\Users\mohitdhande\OneDrive - Microsoft\Documents\Microsoft Scout\Stealth Health Recipes")

names = sys.argv[1:]
for n in names:
    matches = list(SRC.glob(n + "*.pdf"))
    if not matches:
        print("NO MATCH", n); continue
    p = matches[0]
    doc = fitz.open(p)
    print("=" * 80)
    print("FILE:", p.name, "| pages:", len(doc))
    print("=" * 80)
    for i, page in enumerate(doc):
        print(f"----- page {i+1} -----")
        print(page.get_text())
    doc.close()
