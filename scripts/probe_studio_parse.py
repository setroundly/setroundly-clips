"""TikTok Studio DOM scrape probe — parsers only (no browser).

Validated 2026-06-03 against live Studio via Cursor IDE browser + CDP Runtime.evaluate.
Run: python scripts/probe_studio_parse.py

Agent flow (production):
  1) Navigate Posts or Analytics > Content
  2) Click "View data" -> /tiktokstudio/analytics/{item_id}/overview
  3) document.body.innerText -> parse_overview_text()
  4) update_results.py --stdin
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict


@dataclass
class OverviewMetrics:
    analytics_item_id: str | None
    caption: str | None
    posted_date: str | None
    views: float | None
    likes: float | None
    comments: float | None
    shares: float | None
    saves: float | None
    avg_watch_s: float | None
    full_watch_rate: float | None
    total_play_time: str | None
    retention_note: str | None
    sec2_rate: float | None  # not always on Studio web; often N/A


def _num(s: str) -> float | None:
    s = s.strip().replace(",", "")
    if not s or s in ("-", "<0.1%"):
        return None
    mult = 1.0
    if s.endswith("K"):
        mult = 1_000
        s = s[:-1]
    elif s.endswith("M"):
        mult = 1_000_000
        s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def parse_overview_text(text: str, url: str = "") -> OverviewMetrics:
    """Parse TikTok Studio per-video Overview tab innerText."""
    item_id = None
    m = re.search(r"/analytics/(\d+)/", url)
    if m:
        item_id = m.group(1)

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    caption = posted = None
    for i, ln in enumerate(lines):
        if ln.startswith("Posted on "):
            posted = ln.replace("Posted on ", "").strip()
            if i > 0:
                caption = lines[i - 1]
            break

    views = avg_watch = full_watch = None
    total_play = retention_note = None
    for i, ln in enumerate(lines):
        if ln == "Video views" and i + 1 < len(lines):
            views = _num(lines[i + 1])
        elif ln == "Average watch time" and i + 1 < len(lines):
            avg_watch = _num(lines[i + 1].replace("s", ""))
        elif ln == "Watched full video" and i + 1 < len(lines):
            full_watch = _num(lines[i + 1].replace("%", ""))
        elif ln == "Total play time" and i + 1 < len(lines):
            total_play = lines[i + 1]
        elif ln == "Retention rate" and i + 1 < len(lines):
            retention_note = lines[i + 1]

    # Header block often: views, likes, comments, shares, saves (single line each after caption)
    likes = comments = shares = saves = None
    if caption and posted:
        try:
            idx = lines.index(f"Posted on {posted}")
            nums = []
            for ln in lines[idx + 1 : idx + 8]:
                if ln in (
                    "Video views", "Overview", "Viewers", "Engagement",
                    "Updated in real time.",
                ):
                    break
                if re.fullmatch(r"[\d.,]+[KkMm%]?", ln):
                    nums.append(_num(ln.replace("%", "")))
            if len(nums) >= 1:
                views = views or nums[0]
            if len(nums) >= 2:
                likes = nums[1]
            if len(nums) >= 3:
                comments = nums[2]
            if len(nums) >= 4:
                shares = nums[3]
            if len(nums) >= 5:
                saves = nums[4]
        except ValueError:
            pass

    sec2 = None
    m2 = re.search(r"0:02\s*\((\d+(?:\.\d+)?)%\)", text)
    if m2:
        sec2 = float(m2.group(1))

    return OverviewMetrics(
        analytics_item_id=item_id,
        caption=caption,
        posted_date=posted,
        views=views,
        likes=likes,
        comments=comments,
        shares=shares,
        saves=saves,
        avg_watch_s=avg_watch,
        full_watch_rate=full_watch,
        total_play_time=total_play,
        retention_note=retention_note,
        sec2_rate=sec2,
    )


def parse_posts_list_text(text: str) -> list[dict]:
    """Parse Posts (/tiktokstudio/content) table innerText into rows."""
    rows = []
    # Pattern: duration line, caption block, date, Everyone, views, likes, comments
    chunks = re.split(
        r"(?=\d{2}:\d{2}\n)",
        text,
    )
    for chunk in chunks:
        if "Everyone" not in chunk:
            continue
        lines = [x.strip() for x in chunk.splitlines() if x.strip()]
        if len(lines) < 4:
            continue
        dur = lines[0]
        nums = re.findall(r"^(\d[\d,]*)$", "\n".join(lines))
        tail = lines[-3:]
        if len(tail) >= 3 and all(re.fullmatch(r"\d+", t) for t in tail):
            rows.append({
                "duration": dur,
                "caption": " ".join(lines[1:-4])[:120],
                "views": int(tail[0].replace(",", "")),
                "likes": int(tail[1]),
                "comments": int(tail[2]),
            })
    return rows


# --- fixture from live probe 2026-06-03 ---
SAMPLE_OVERVIEW = """
Updated in real time.
Overview
Viewers
Engagement
全部どうでもよかった日に、できた曲。 ハニーハニー / SETROUNDLY #弾き語り
Posted on 6/1/2026
389
8
0
1
3
Video views
389
Total play time
1h:31m:20s
Average watch time
11.32s
Watched full video
13.2%
Retention rate
Most viewers stopped watching at 0:01.
"""

SAMPLE_POSTS = """
Posts 32
00:18
見せかけの優しさは、いらなかった。
Jun 4, 6:00 PM
Everyone
220
8
0
"""


if __name__ == "__main__":
    url = "https://www.tiktok.com/tiktokstudio/analytics/7645966746758712592/overview"
    ov = parse_overview_text(SAMPLE_OVERVIEW, url)
    print("=== overview parse ===")
    print(json.dumps(asdict(ov), ensure_ascii=False, indent=2))

    posts = parse_posts_list_text(SAMPLE_POSTS)
    print("\n=== posts list parse ===")
    print(json.dumps(posts, ensure_ascii=False, indent=2))

    print("\nOK: parsers run. Wire to browser via agent CDP or Playwright (see TIKTOK_SCRAPE_FEASIBILITY.md).")
