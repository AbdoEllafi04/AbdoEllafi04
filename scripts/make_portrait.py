#!/usr/bin/env python3
"""
Turn a photo into an animated ASCII portrait (portrait-ascii.svg, 840x880)
that 'prints' line by line inside a terminal window.

Photo source, first match wins:
  1. a path passed as the first argument
  2. source-photo.png / .jpg / .jpeg in the repo root
  3. your GitHub avatar (https://github.com/<username>.png)

If the optional `rembg` package is installed, the background is removed first;
otherwise a soft oval vignette fades the edges out.
"""
import io
import os
import sys

from PIL import Image, ImageFilter, ImageOps

from common import ACCENT, INK, PROFILE, ROOT, TYPE_CSS, esc, prompt, window

OUT = os.path.join(ROOT, "portrait-ascii.svg")
W, H = 840, 880
COLS = 92
CW = (W - 48) / COLS            # char cell width in px
LH = CW * 1.5                   # line height
ROWS = int((H - 37 - 20 - 70) / LH)
FONT = CW / 0.6
RAMP = " .'`:,;-~=+i*ox#%&@"    # dark -> bright (bright = dense on a dark bg)
SHADES = [(0.30, "s0"), (0.55, "s1"), (0.78, "s2"), (1.01, "s3")]


def load_photo():
    if len(sys.argv) > 1:
        return Image.open(sys.argv[1])
    for name in ("source-photo.png", "source-photo.jpg", "source-photo.jpeg"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            return Image.open(p)
    import requests
    url = f"https://github.com/{PROFILE['username']}.png?size=460"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))


def cut_background(img):
    """Return (RGB image, alpha mask). Uses rembg when available."""
    img = ImageOps.exif_transpose(img).convert("RGBA")
    try:
        from rembg import new_session, remove  # optional
        model = os.environ.get("REMBG_MODEL", "u2net_human_seg")   # ~170 MB, made for people
        cut = remove(img, session=new_session(model))
        print(f"background removed with rembg ({model})")
        return cut.convert("RGB"), cut.getchannel("A")
    except Exception as e:  # not installed or failed: fall back to a vignette
        print(f"rembg unavailable ({e.__class__.__name__}); using vignette")
        w, h = img.size
        mask = Image.new("L", (w, h), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(mask).ellipse([w * 0.08, h * 0.02, w * 0.92, h * 1.15], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(w * 0.06))
        return img.convert("RGB"), mask


def to_grid(img, mask):
    # zoom to the subject first so the face fills the frame
    bbox = mask.point(lambda v: 255 if v > 128 else 0).getbbox()
    if bbox:
        pad = int(0.04 * max(img.size))
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(img.width, bbox[2] + pad), min(img.height, bbox[3] + pad))
        img, mask = img.crop(bbox), mask.crop(bbox)
    # crop to the aspect ratio of the character grid (cells are taller than wide)
    target = (COLS * CW) / (ROWS * LH)
    w, h = img.size
    if w / h > target:
        nw = int(h * target)
        box = ((w - nw) // 2, 0, (w - nw) // 2 + nw, h)
    else:
        nh = int(w / target)
        box = (0, 0, w, nh)              # keep the top: that's where the face is
    img, mask = img.crop(box), mask.crop(box)

    gray = ImageOps.grayscale(img)
    subject = mask.point(lambda v: 255 if v > 128 else 0)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=160, threshold=2))
    gray = gray.resize((COLS, ROWS), Image.LANCZOS)
    # spread the subject's tones evenly so eyes, nose and mouth stay readable
    small_subject = subject.resize((COLS, ROWS), Image.LANCZOS).point(lambda v: 255 if v > 128 else 0)
    gray = ImageOps.equalize(gray, mask=small_subject)
    gray = gray.point(lambda v: int(255 * (v / 255) ** 1.15))
    mask = mask.resize((COLS, ROWS), Image.LANCZOS)

    rows = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            a = mask.getpixel((x, y)) / 255
            b = gray.getpixel((x, y)) / 255 * a
            if a < 0.35 or b < 0.10:
                row.append((" ", None))
                continue
            ch = RAMP[min(len(RAMP) - 1, int(b * len(RAMP)))]
            shade = next(c for lim, c in SHADES if b < lim)
            row.append((ch, shade))
        rows.append(row)
    # trim empty rows at the bottom/top so the face sits nicely
    while rows and all(c == " " for c, _ in rows[-1]):
        rows.pop()
    return rows


def render(rows):
    top = 37 + 22 + FONT
    offset = (ROWS - len(rows)) * LH / 2
    body, t = [], 0.2
    step = 2.6 / max(len(rows), 1)
    for i, row in enumerate(rows):
        y = top + offset + i * LH
        # group runs of the same shade into tspans
        spans, cur, buf = [], None, ""
        for ch, shade in row:
            if shade != cur and buf:
                spans.append((cur, buf))
                buf = ""
            cur, buf = shade, buf + ch
        spans.append((cur, buf))
        if all(s is None for s, _ in spans):
            continue
        inner = "".join(f'<tspan class="{s}">{esc(b)}</tspan>' if s else esc(b) for s, b in spans)
        cid = f"l{i}"
        delay = t + i * step
        body.append(
            f'<clipPath id="{cid}"><rect class="type" x="24" y="{y - FONT:.1f}" width="{COLS * CW:.1f}" '
            f'height="{LH + 2:.1f}" style="animation-delay:{delay:.2f}s"/></clipPath>'
            f'<text x="24" y="{y:.1f}" font-size="{FONT:.2f}" xml:space="preserve" clip-path="url(#{cid})" '
            f'textLength="{COLS * CW:.1f}" lengthAdjust="spacingAndGlyphs">{inner}</text>')
    t += len(rows) * step + 0.3

    name = PROFILE["name"]
    body.append(prompt(24, H - 26, f"whoami  # {name}", delay=t, cursor=True))
    css = (TYPE_CSS +
           f".s0{{fill:{ACCENT};opacity:.35}}.s1{{fill:{ACCENT};opacity:.6}}"
           f".s2{{fill:{ACCENT};opacity:.85}}.s3{{fill:{INK}}}")
    return window(W, H, f"{PROFILE.get('prompt_user', 'abdo')}@github: ~$ ./portrait.sh", "\n".join(body), css)


def main():
    img, mask = cut_background(load_photo())
    rows = to_grid(img, mask)
    svg = render(rows)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(rows)} rows x {COLS} cols, {len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
