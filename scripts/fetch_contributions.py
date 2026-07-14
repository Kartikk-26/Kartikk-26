#!/usr/bin/env python3
"""
Scrape real daily contribution counts from GitHub's public, unauthenticated
contributions endpoint (the same fragment the profile page itself uses) and
write data/contributions.json.

IMPORTANT: that endpoint only serves a ROLLING 12-MONTH window. Asking it once
gives you at most ~366 days, which silently caps totals and makes any streak
longer than a year impossible to see. So we walk it year-by-year from
ACCOUNT_START_YEAR using the ?from=&to= params and merge the days.

Output carries both:
  - all-time stats (total, true current/longest streak, best day)
  - a last-53-week window ("days") that the heatmap grid renders

No token, no auth, no GraphQL -- just the public HTML GitHub already serves.
Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

from profile_config import ACCOUNT_START_YEAR, GITHUB_USER

USERNAME = os.environ.get("GH_PROFILE_USER", GITHUB_USER)
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")

HEADERS = {"User-Agent": "profile-readme-bot/1.0"}
GRID_WEEKS = 53  # what the heatmap actually draws


def fetch_window(from_date, to_date):
    """Fetch one <=1y window; returns {date: count}."""
    url = (f"https://github.com/users/{USERNAME}/contributions"
           f"?from={from_date}&to={to_date}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print(f"no calendar cells for {from_date}..{to_date} -- markup may have changed",
              file=sys.stderr)
        return {}

    out = {}
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        td_id = td.get("id")
        tooltip_el = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        text = tooltip_el.get_text(strip=True) if tooltip_el else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"([\d,]+)", text)
            count = int(m.group(1).replace(",", "")) if m else 0
        out[date] = count
    return out


def fetch_all_days():
    """Walk year-by-year so streaks/totals aren't clipped to a rolling year."""
    today = datetime.date.today()
    merged = {}
    for year in range(ACCOUNT_START_YEAR, today.year + 1):
        start = datetime.date(year, 1, 1)
        end = min(datetime.date(year, 12, 31), today)
        got = fetch_window(start.isoformat(), end.isoformat())
        # Two kinds of junk cells to drop:
        #  - neighbouring-year padding (endpoint pads the grid) -> double counting
        #  - future dates in the current year, which come back as zeros and would
        #    otherwise read as "streak broken" and zero out the current streak
        today_s = today.isoformat()
        got = {d: c for d, c in got.items()
               if d[:4] == str(year) and d <= today_s}
        merged.update(got)
        print(f"  {year}: {len(got)} days, {sum(got.values())} contributions",
              file=sys.stderr)

    if not merged:
        print("no contribution data found at all", file=sys.stderr)
        sys.exit(1)

    days = [{"date": d, "count": c} for d, c in sorted(merged.items())]
    # drop the zero-days before the account's first real contribution
    first_active = next((i for i, d in enumerate(days) if d["count"] > 0), 0)
    return days[first_active:]


def compute_current_streak(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # today isn't over yet -- don't break the streak on it
    streak = 0
    end_idx = idx
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    start_idx = idx + 1
    if streak == 0:
        return 0, None, None
    return streak, days[start_idx]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start_idx = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start_idx = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start_idx]["date"]
                longest_end = days[i]["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(all_days):
    total = sum(d["count"] for d in all_days)
    active_days = sum(1 for d in all_days if d["count"] > 0)
    best = max(all_days, key=lambda d: d["count"])
    cur_len, cur_start, cur_end = compute_current_streak(all_days)
    long_len, long_start, long_end = compute_longest_streak(all_days)

    # window the heatmap grid renders: last 53 weeks, snapped back to a Sunday
    today = datetime.date.today()
    window_start = today - datetime.timedelta(weeks=GRID_WEEKS)
    window_start -= datetime.timedelta(days=(window_start.weekday() + 1) % 7)
    grid_days = [d for d in all_days
                 if datetime.date.fromisoformat(d["date"]) >= window_start]
    last_year_total = sum(d["count"] for d in grid_days)

    monthly = {}
    for d in all_days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    monthly_list = [{"month": k, "total": v} for k, v in sorted(monthly.items())]

    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
                                .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": all_days[0]["date"], "end": all_days[-1]["date"]},
        "total_contributions": total,
        "last_year_contributions": last_year_total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly_list,
        "grid_range": {"start": grid_days[0]["date"], "end": grid_days[-1]["date"]},
        "days": grid_days,   # heatmap grid (last ~year)
    }


if __name__ == "__main__":
    all_days = fetch_all_days()
    data = build_data(all_days)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT_PATH}: {data['total_contributions']:,} all-time contributions "
          f"({data['last_year_contributions']:,} in the last year), "
          f"current streak {data['current_streak']['length']}, "
          f"longest streak {data['longest_streak']['length']}")
