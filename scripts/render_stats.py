#!/usr/bin/env python3
"""Render stats.svg (840x880, same canvas as portrait-ascii.svg): a neofetch-style
'whoami' block from profile.json plus streaks, totals and monthly bars from
data/contributions.json."""
import datetime as dt
import os

from common import (ACCENT, BORDER, DIM, INK, LEVELS, PROFILE, ROOT, TYPE_CSS,
                    esc, load_data, prompt, window)

OUT = os.path.join(ROOT, "stats.svg")
W, H = 840, 880
PAD = 24
MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
WEEKDAYS = "Sundays Mondays Tuesdays Wednesdays Thursdays Fridays Saturdays".split()


def short(d):
    if not d:
        return ""
    d = dt.date.fromisoformat(d)
    return f"{MON[d.month - 1]} {d.day}"


def span(s):
    if not s["length"]:
        return "start one today"
    return short(s["start"]) if s["start"] == s["end"] else f'{short(s["start"])} → {short(s["end"])}'


def line(y, delay, label, value, sub=""):
    return (f'<g class="row" style="animation-delay:{delay:.2f}s">'
            f'<text x="{PAD + 8}" y="{y}" font-size="15" class="dim">{esc(label)}</text>'
            f'<text x="{PAD + 210}" y="{y}" font-size="15" class="ink" font-weight="600">{esc(value)}'
            + (f'<tspan class="dim" font-weight="400">  {esc(sub)}</tspan>' if sub else "")
            + "</text></g>")


def main():
    d = load_data()
    t = 0.1
    out = [prompt(PAD, 72, "neofetch", delay=t)]

    # --- whoami block -------------------------------------------------------
    t += 0.7
    name = PROFILE["name"]
    out.append(f'<g class="row" style="animation-delay:{t:.2f}s">'
               f'<text x="{PAD + 8}" y="116" font-size="26" font-weight="700" fill="{ACCENT}">{esc(name)}</text>'
               f'<rect x="{PAD + 8}" y="128" width="{min(len(name) * 15.6, W - 2 * PAD)}" height="2" fill="{BORDER}"/></g>')
    y = 162
    for key, val in PROFILE["info"]:
        t += 0.12
        out.append(line(y, t, key, val))
        y += 28

    # --- stats ---------------------------------------------------------------
    y += 18
    t += 0.3
    out.append(prompt(PAD, y, "./stats.sh", delay=t))
    t += 0.7

    def days_word(n):
        return "day" if n == 1 else "days"

    cs, ls = d["current_streak"]["length"], d["longest_streak"]["length"]
    tiles = [
        ("CURRENT STREAK", f"{cs}", days_word(cs), span(d["current_streak"])),
        ("LONGEST STREAK", f"{ls}", days_word(ls), span(d["longest_streak"])),
        ("CONTRIBUTIONS", f'{d["total"]:,}', "", "last 12 months"),
    ]
    ty = y + 22
    tw = (W - 2 * PAD - 2 * 16) / 3
    for i, (label, big, unit, sub) in enumerate(tiles):
        x = PAD + i * (tw + 16)
        out.append(
            f'<g class="row" style="animation-delay:{t + i * 0.15:.2f}s">'
            f'<rect x="{x:.1f}" y="{ty}" width="{tw:.1f}" height="112" rx="8" fill="#161b22" stroke="{BORDER}"/>'
            f'<text x="{x + 16:.1f}" y="{ty + 26}" font-size="11" letter-spacing="1.5" class="dim">{label}</text>'
            f'<text x="{x + 16:.1f}" y="{ty + 72}" font-size="40" font-weight="700" fill="{ACCENT if i == 0 else INK}">{big}'
            + (f'<tspan font-size="15" font-weight="400" class="dim"> {unit}</tspan>' if unit else "")
            + f'</text><text x="{x + 16:.1f}" y="{ty + 96}" font-size="12" class="dim">{esc(sub)}</text></g>')
    t += 0.6

    y = ty + 150
    days_total = len(d["days"])
    wd = d.get("weekday") or [0] * 7
    rows = [
        ("active days", f'{d["active_days"]} / {days_total}', f'{round(100 * d["active_days"] / days_total)}%'),
        ("best day", f'{d["best_day"]["count"]}', f'on {short(d["best_day"]["date"])}' if d["best_day"]["count"] else ""),
        ("avg / active day", f'{d["avg_per_active_day"]}', ""),
        ("busiest weekday", WEEKDAYS[wd.index(max(wd))] if any(wd) else "—", ""),
    ]
    for label, val, sub in rows:
        out.append(line(y, t, label, val, sub))
        t += 0.12
        y += 28

    # --- monthly bars ---------------------------------------------------------
    months = d["monthly"][-12:]
    top = max((m["total"] for m in months), default=0) or 1
    base = 800
    maxh = 120
    gap = 10
    bw = (W - 2 * PAD - 16 - gap * (len(months) - 1)) / max(len(months), 1)
    t += 0.2
    out.append(f'<text x="{PAD + 8}" y="{base - maxh - 16}" font-size="12" class="dim row" '
               f'style="animation-delay:{t:.2f}s">contributions per month</text>')
    for i, m in enumerate(months):
        x = PAD + 8 + i * (bw + gap)
        h = max(3, m["total"] / top * maxh)
        lvl = 0 if not m["total"] else min(4, 1 + int(3.999 * m["total"] / top))
        label = MON[int(m["month"][5:]) - 1]
        out.append(
            f'<rect class="bar" x="{x:.1f}" y="{base - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" '
            f'fill="{LEVELS[max(lvl, 1)] if m["total"] else LEVELS[0]}" style="animation-delay:{t + i * 0.06:.2f}s">'
            f'<title>{m["month"]}: {m["total"]}</title></rect>'
            f'<text x="{x + bw / 2:.1f}" y="{base + 18}" font-size="11" text-anchor="middle" class="dim">{label}</text>')
        if m["total"] == top:
            out.append(f'<text x="{x + bw / 2:.1f}" y="{base - h - 6:.1f}" font-size="11" text-anchor="middle" '
                       f'class="ink row" style="animation-delay:{t + 0.8:.2f}s">{m["total"]}</text>')
    t += 1.2

    out.append(prompt(PAD, H - 26, "", delay=t, cursor=True))
    css = (TYPE_CSS +
           ".row{opacity:0;animation:rise .45s ease-out forwards}"
           "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
           ".bar{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .7s cubic-bezier(.2,.8,.2,1) forwards}"
           "@keyframes grow{to{transform:scaleY(1)}}")
    svg = window(W, H, f"{PROFILE.get('prompt_user', 'abdo')}@github: ~$ whoami", "\n".join(out), css)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
