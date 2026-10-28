#!/usr/bin/env python3
"""Render stack.svg: `ls ~/stack` with each technology popping in as a tag,
grouped by category. Edit the "stack" list in profile.json."""
import os

from common import PROFILE, ROOT, TYPE_CSS, esc, prompt, window

OUT = os.path.join(ROOT, "stack.svg")
W = 860
SIZE = 14                 # tag font size
CW = SIZE * 0.6           # monospace char width
ROW = 46
LABEL_X, TAGS_X = 32, 190


def main():
    groups = PROFILE.get("stack", [])
    body = [prompt(24, 72, "ls ~/stack --by-category", delay=0.1)]
    t, y = 0.9, 116
    for label, color, items in groups:
        body.append(f'<text x="{LABEL_X}" y="{y + 5}" font-size="15" fill="{color}" class="pop" '
                    f'style="animation-delay:{t:.2f}s">{esc(label)}/</text>')
        x = TAGS_X
        for name in items:
            w = len(name) * CW + 26
            if x + w > W - 24:            # wrap long groups onto the next line
                x, y = TAGS_X, y + ROW
            t += 0.12
            body.append(
                f'<g class="pop" style="animation-delay:{t:.2f}s">'
                f'<rect x="{x:.1f}" y="{y - 15}" width="{w:.1f}" height="30" rx="7" '
                f'fill="{color}" fill-opacity=".12" stroke="{color}" stroke-opacity=".55"/>'
                f'<text x="{x + w / 2:.1f}" y="{y + 5}" font-size="{SIZE}" text-anchor="middle" fill="{color}" '
                f'textLength="{len(name) * CW:.1f}" lengthAdjust="spacingAndGlyphs">{esc(name)}</text></g>')
            x += w + 10
        y += ROW
        t += 0.15
    H = int(y + 6)
    css = (TYPE_CSS +
           ".pop{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .45s ease-out forwards}"
           "@keyframes pop{0%{opacity:0;transform:scale(.6)}70%{opacity:1;transform:scale(1.06)}100%{opacity:1;transform:scale(1)}}")
    svg = window(W, H, f"{PROFILE.get('prompt_user', 'abdo')}@github: ~/stack", "\n".join(body), css)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
