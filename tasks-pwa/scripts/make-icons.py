"""Generates the PWA icons into public/. Run: python3 scripts/make-icons.py"""
from PIL import Image, ImageDraw

def icon(size: int, path: str) -> None:
    s = size * 4  # supersample for smooth edges
    img = Image.new("RGB", (s, s), "#007aff")
    d = ImageDraw.Draw(img)
    w = s // 11
    pts = [(s * 0.27, s * 0.52), (s * 0.43, s * 0.68), (s * 0.74, s * 0.35)]
    d.line(pts, fill="white", width=w, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill="white")
    img.resize((size, size), Image.LANCZOS).save(path)

for size, name in ((180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")):
    icon(size, f"public/{name}")
