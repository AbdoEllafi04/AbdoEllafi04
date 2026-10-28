#!/usr/bin/env python3
"""
Scrape your real daily contribution counts from GitHub's public contributions
fragment (the same HTML your profile page loads) and save them, together with
derived stats, to data/contributions.json.

No token needed. Run daily by .github/workflows/update-profile-art.yml.

    GH_PROFILE_USER=AbdoEllafi04 python scripts/fetch_contributions.py
"""
import datetime as dt
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_PROFILE_USER", "AbdoEllafi04")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "contributions.json")


def fetch_days(user):
    url = f"https://github.com/users/{user}/contributions"
    r = requests.get(url, headers={"User-Agent": "profile-art/1.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        text = tips.get(td.get("id"), "")
        m = re.match(r"\s*(\d[\d,]*)", text)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({
            "date": td["data-date"],
            "count": count,
            "level": int(td.get("data-level") or 0),
        })
    if not days:
        sys.exit("no calendar cells found - GitHub markup may have changed")
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    # longest run of days with >0 contributions
    best = run = 0
    best_span = (None, None)
    start = None
    for d in days:
        if d["count"]:
            start = d["date"] if run == 0 else start
            run += 1
            if run > best:
                best, best_span = run, (start, d["date"])
        else:
            run = 0

    # current streak: today doesn't break it if it's still empty
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1
    end = i
    while i >= 0 and days[i]["count"]:
        i -= 1
    cur = end - i
    cur_span = (days[i + 1]["date"], days[end]["date"]) if cur else (None, None)
    return (cur, cur_span), (best, best_span)


def build(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    (cur, cur_span), (best, best_span) = streaks(days)
    top = max(days, key=lambda d: d["count"])

    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    weekday = [0] * 7  # Sun..Sat
    for d in days:
        weekday[(dt.date.fromisoformat(d["date"]).weekday() + 1) % 7] += d["count"]

    return {
        "username": USER,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": {"length": cur, "start": cur_span[0], "end": cur_span[1]},
        "longest_streak": {"length": best, "start": best_span[0], "end": best_span[1]},
        "best_day": {"date": top["date"], "count": top["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "weekday": weekday,
        "days": days,
    }


if __name__ == "__main__":
    data = build(fetch_days(USER))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print(f"{USER}: {data['total']} contributions, "
          f"current streak {data['current_streak']['length']}, "
          f"longest {data['longest_streak']['length']}")
