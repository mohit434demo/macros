"""Generate app icons (sage ring mark) without external assets."""
import pathlib, math
from PIL import Image, ImageDraw

OUT = pathlib.Path(__file__).parent.parent / "site" / "icons"
OUT.mkdir(parents=True, exist_ok=True)

BG = (244, 242, 236)
SAGE = (107, 143, 107)
SAGE_LIGHT = (196, 213, 191)
CLAY = (184, 154, 94)


def make(size, maskable=False):
    ss = 4
    S = size * ss
    img = Image.new("RGBA", (S, S), BG + (255,))
    d = ImageDraw.Draw(img)

    # maskable icons must keep art inside the safe zone (inner 80%)
    scale = 0.62 if maskable else 0.78
    r = S * scale / 2
    cx = cy = S / 2
    w = S * (0.085 if maskable else 0.10)

    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=SAGE_LIGHT + (255,), width=int(w))
    # progress arc, three quarters round
    d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=180, fill=SAGE + (255,), width=int(w))

    # fork-free wordless mark: a leaf inside the ring
    lr = r * 0.52
    leaf = [
        (cx, cy - lr),
        (cx + lr * 0.78, cy - lr * 0.05),
        (cx, cy + lr),
        (cx - lr * 0.78, cy - lr * 0.05),
    ]
    d.polygon(leaf, fill=SAGE + (255,))
    d.line([(cx, cy - lr * 0.85), (cx, cy + lr * 0.9)], fill=BG + (255,), width=max(2, int(S * 0.016)))
    for t in (0.28, 0.55):
        y = cy - lr + (2 * lr) * t
        span = lr * 0.55 * (1 - abs(t - 0.45) * 1.2)
        d.line([(cx, y), (cx - span, y + span * 0.55)], fill=BG + (255,), width=max(2, int(S * 0.012)))
        d.line([(cx, y), (cx + span, y + span * 0.55)], fill=BG + (255,), width=max(2, int(S * 0.012)))

    return img.resize((size, size), Image.LANCZOS)


for size in (192, 512):
    make(size).save(OUT / f"icon-{size}.png")
make(512, maskable=True).save(OUT / "icon-maskable.png")
make(180).save(OUT / "apple-touch-icon.png")
print("icons written to", OUT)
for p in sorted(OUT.iterdir()):
    print("  ", p.name, p.stat().st_size, "bytes")
