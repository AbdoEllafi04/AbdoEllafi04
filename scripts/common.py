"""Shared bits for the profile-art scripts: config, palette, terminal frame."""
import hashlib
import html
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

with open(os.path.join(ROOT, "profile.json"), encoding="utf-8") as f:
    PROFILE = json.load(f)

HANDLE = PROFILE.get("prompt_user", "abdo")       # shows up as abdo@github
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# palette (GitHub dark)
BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
INK = "#e6edf3"
DIM = "#7d8590"
GREEN = "#3fb950"
BLUE = "#58a6ff"
ACCENT = PROFILE.get("accent", "#54c5f8")         # Flutter blue
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def esc(s):
    return html.escape(str(s), quote=True)


def load_data():
    with open(os.path.join(ROOT, "data", "contributions.json"), encoding="utf-8") as f:
        return json.load(f)


def window(w, h, title, body, extra_css=""):
    """Wrap SVG body content in a macOS-style terminal window."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{MONO}">
<style>
text{{font-family:{MONO}}}
.dim{{fill:{DIM}}} .ink{{fill:{INK}}} .grn{{fill:{GREEN}}} .blu{{fill:{BLUE}}} .acc{{fill:{ACCENT}}}
.cur{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
{extra_css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important;transform:none!important}}}}
</style>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
<path d="M0.5 12.5a12 12 0 0 1 12-12h{w-25}a12 12 0 0 1 12 12v24h-{w-1}z" fill="{BAR}"/>
<line x1="0.5" y1="36.5" x2="{w-0.5}" y2="36.5" stroke="{BORDER}"/>
<circle cx="22" cy="18.5" r="6" fill="#ff5f57"/><circle cx="42" cy="18.5" r="6" fill="#febc2e"/><circle cx="62" cy="18.5" r="6" fill="#28c840"/>
<text x="{w/2}" y="23" font-size="13" text-anchor="middle" class="dim">{esc(title)}</text>
{body}
</svg>
'''


def prompt(x, y, cmd, size=15, delay=0.0, cursor=False):
    """A shell prompt line: abdo@github:~$ <cmd>, typed in with a clip."""
    who = f"{HANDLE}@github"
    full = f"{who}:~$ {cmd}"
    cw = size * 0.6
    width = len(full) * cw
    cid = "p" + hashlib.md5(f"{x},{y},{cmd}".encode()).hexdigest()[:8]  # stable across runs
    cur = ""
    if cursor:
        cur = (f'<rect class="cur" x="{x + width + 2:.1f}" y="{y - size + 3}" width="{cw:.1f}" '
               f'height="{size}" fill="{INK}" style="animation-delay:{delay + 0.6}s"/>')
    return f'''<clipPath id="{cid}"><rect class="type" x="{x}" y="{y - size}" width="{width + 4:.1f}" height="{size + 6}" style="animation-delay:{delay}s"/></clipPath>
<text x="{x}" y="{y}" font-size="{size}" clip-path="url(#{cid})" textLength="{width:.1f}" lengthAdjust="spacingAndGlyphs"><tspan class="grn">{esc(who)}</tspan><tspan class="ink">:</tspan><tspan class="blu">~</tspan><tspan class="ink">$ {esc(cmd)}</tspan></text>{cur}'''


TYPE_CSS = (".type{transform-box:fill-box;transform-origin:left;transform:scaleX(0);"
            "animation:type .7s steps(28,end) forwards}"
            "@keyframes type{to{transform:scaleX(1)}}")
