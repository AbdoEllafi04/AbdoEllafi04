#!/usr/bin/env python3
"""Render intro.svg: a short greeting that types itself out, letter by letter,
in a terminal window. Edit the "intro" lines in profile.json."""
import os

from common import ACCENT, INK, PROFILE, ROOT, TYPE_CSS, esc, prompt, window

OUT = os.path.join(ROOT, "intro.svg")
W = 860
SPEED = 0.045            # seconds per character


def typed(x, y, text, size, delay, cls="ink", weight=400):
    """One line that types in char by char (monospace width pinned via textLength)."""
    n = len(text)
    width = n * size * 0.6
    dur = max(0.4, n * SPEED)
    cid = f"t{int(y)}"
    return (f'<clipPath id="{cid}"><rect class="type" x="{x}" y="{y - size}" width="{width + 2:.1f}" '
            f'height="{size + 8}" style="animation:type {dur:.2f}s steps({n},end) {delay:.2f}s forwards"/></clipPath>'
            f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" class="{cls}" '
            f'clip-path="url(#{cid})" textLength="{width:.1f}" lengthAdjust="spacingAndGlyphs">{esc(text)}</text>'), \
        delay + dur, width


def main():
    lines = PROFILE.get("intro") or [f"Hi, I'm {PROFILE['name']}."]
    body = [prompt(24, 72, 'echo "$HELLO"', delay=0.1)]
    t, y = 1.0, 116
    last_w, last_y, last_size = 0, y, 24
    for i, text in enumerate(lines):
        size = 24 if i == 0 else 16
        part, t, last_w = typed(24, y, text, size, t, "ink" if i == 0 else "dim", 700 if i == 0 else 400)
        body.append(part)
        last_y, last_size = y, size
        y += 36 if i == 0 else 28
        t += 0.25
    # blinking cursor right after the last line, shown once typing is done
    body.append(f'<rect class="cur" x="{24 + last_w + 4:.1f}" y="{last_y - last_size + 3}" '
                f'width="{last_size * 0.6:.1f}" height="{last_size}" fill="{ACCENT}" '
                f'style="opacity:0;animation:show 0s {t:.2f}s forwards,blink 1s steps(1) {t:.2f}s infinite"/>')
    H = int(y + 8)
    css = TYPE_CSS + "@keyframes show{to{opacity:1}}"
    svg = window(W, H, f"{PROFILE.get('prompt_user', 'abdo')}@github: ~", "\n".join(body), css)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
