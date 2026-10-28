#!/usr/bin/env python3
"""Render data/contributions.json as an animated contribution graph
(contrib-heatmap.svg): cells pop in week by week inside a terminal window."""
import datetime as dt
import math
import os

from common import (DIM, INK, LEVELS, ROOT, TYPE_CSS, esc, load_data, prompt,
                    window)

OUT = os.path.join(ROOT, "contrib-heatmap.svg")
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

CELL, GAP = 12, 3
STEP = CELL + GAP
LEFT, TOP = 58, 112
START = 0.9          # seconds: wait for the prompt to type
SPAN = 3.2           # seconds for the whole grid to fill


def relevel(days):
    """GitHub shades cells relative to your single busiest day, so a few huge
    days push everything else into the palest green. Shade on a log scale up to
    a typical busy day (95th percentile) instead, so the graph shows real variety."""
    active = sorted(d["count"] for d in days if d["count"])
    if not active:
        return
    p95 = active[min(len(active) - 1, int(0.95 * len(active)))]
    for d in days:
        c = d["count"]
        if not c:
            d["level"] = 0
        elif p95 <= 1:
            d["level"] = 1
        else:
            d["level"] = max(1, min(4, 1 + round(3 * math.log(c) / math.log(p95))))


def main():
    data = load_data()
    days = data["days"]
    relevel(days)
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7            # GitHub rows start on Sunday
    weeks = (offset + len(days) + 6) // 7

    W = max(860, LEFT + weeks * STEP + 30)
    H = 272

    cells, labels = [], []
    last_month, starts = None, []
    for i, d in enumerate(days):
        idx = i + offset
        wk, row = divmod(idx, 7)
        x, y = LEFT + wk * STEP, TOP + row * STEP
        delay = START + (wk + row * 0.6) / (weeks + 4) * SPAN
        cls = "c on" if d["level"] else "c"
        cells.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                     f'fill="{LEVELS[d["level"]]}" style="animation-delay:{delay:.2f}s"/>')
        day = dt.date.fromisoformat(d["date"])
        if (row == 0 or i == 0) and day.month != last_month:
            starts.append((wk, day.month))
            last_month = day.month
    # one label per month; drop a label crowded by the next one (partial first month)
    for k, (wk, month) in enumerate(starts):
        nxt = starts[k + 1][0] if k + 1 < len(starts) else weeks + 3
        if nxt - wk >= 3:
            labels.append(f'<text x="{LEFT + wk * STEP}" y="{TOP - 9}" font-size="11" class="dim">{MONTHS[month - 1]}</text>')
    for name, r in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        labels.append(f'<text x="{LEFT - 34}" y="{TOP + r * STEP + 10}" font-size="11" class="dim">{name}</text>')

    end = START + SPAN + 0.6
    total = f'{data["total"]:,} contributions in the last year'
    legend_x = LEFT + weeks * STEP - 5 * STEP - 74
    legend = [f'<text x="{legend_x}" y="{TOP + 7 * STEP + 30}" font-size="11" class="dim">Less</text>']
    for k, col in enumerate(LEVELS):
        legend.append(f'<rect x="{legend_x + 34 + k * STEP}" y="{TOP + 7 * STEP + 20}" width="{CELL}" '
                      f'height="{CELL}" rx="2.5" fill="{col}"/>')
    legend.append(f'<text x="{legend_x + 40 + 5 * STEP}" y="{TOP + 7 * STEP + 30}" font-size="11" class="dim">More</text>')

    body = "\n".join([
        prompt(24, 72, "./contributions.sh --graph", delay=0.1),
        *labels, *cells,
        f'<g class="fade" style="animation-delay:{end:.2f}s">'
        f'<text x="{LEFT}" y="{TOP + 7 * STEP + 31}" font-size="14" fill="{INK}" font-weight="700">{esc(total)}</text>'
        + "".join(legend) + "</g>",
    ])
    css = (TYPE_CSS +
           ".c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .5s ease-out forwards}"
           ".on{animation:pop .5s ease-out forwards,glow .9s ease-out forwards}"
           "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:scale(1)}}"
           "@keyframes glow{0%,40%{filter:brightness(2.2)}100%{filter:brightness(1)}}"
           ".fade{opacity:0;animation:fade .6s ease-out forwards}@keyframes fade{to{opacity:1}}")
    svg = window(W, H, f"{data['username']} — contributions", body, css)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(days)} days, {len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
