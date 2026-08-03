"""Check what external links exist: PDF link annotations + Shopify CDN reachability."""
import fitz, json, pathlib, urllib.request, collections

SRC = pathlib.Path(r"C:\Users\mohitdhande\OneDrive - Microsoft\Documents\Microsoft Scout\Stealth Health Recipes")

print("=== link annotations inside PDFs ===")
hosts = collections.Counter()
samples = {}
withlink = 0
for pdf in sorted(SRC.glob("*.pdf")):
    doc = fitz.open(pdf)
    found = []
    for page in doc:
        for l in page.get_links():
            uri = l.get("uri")
            if uri:
                found.append(uri)
    doc.close()
    if found:
        withlink += 1
        for u in found:
            h = u.split("/")[2] if "//" in u else u[:30]
            hosts[h] += 1
            samples.setdefault(h, (pdf.name, u))

print(f"PDFs with links: {withlink} of {len(list(SRC.glob('*.pdf')))}")
for h, n in hosts.most_common():
    print(f"  {n:>4}  {h}")
    print(f"         e.g. {samples[h][1][:110]}")

print("\n=== Shopify CDN reachability (public?) ===")
idx = json.loads((SRC / "index.json").read_text(encoding="utf-8"))
print("entries in index.json:", len(idx))
for e in idx[:3]:
    url = e["url"]
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"  {r.status}  {r.headers.get('Content-Type')}  {e['file'][:44]}")
    except Exception as ex:
        print(f"  ERR {ex}  {e['file'][:44]}")
