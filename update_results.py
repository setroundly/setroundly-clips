#!/usr/bin/env python3
"""Append or update TikTok Studio insights in results.csv.

Usage:
  python update_results.py --init
      Create results.csv / results_template.csv with headers (and rows from tiktok_posts.csv).

  python update_results.py --video-id 7645966686616702224 --views 1200 --two-sec-retention 48%
      Append or update one row (empty / omitted fields are OK).

  python update_results.py --json row.json
      One object or a list of objects with RESULT_FIELDS keys.

  python update_results.py --import-csv studio_export.csv
      Import rows when column names match (extra columns ignored).

  python update_results.py --stdin
      Read JSON lines from stdin (one object per line).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from results_schema import EMPTY_MARKERS, POSTS, RES, RESULT_FIELDS, TPL

ROOT = Path(__file__).resolve().parent

# CLI / import aliases → canonical column names
FIELD_ALIASES = {
    "posted_date": "date",
    "caption": "title",
    "sec2_rate": "two_sec_retention",
    "sec2": "two_sec_retention",
    "2秒維持率": "two_sec_retention",
    "5秒維持率": "five_sec_retention",
    "avg_watch_s": "avg_watch_time",
    "平均視聴時間": "avg_watch_time",
    "完走率": "full_watch_rate",
    "フル視聴率": "full_watch_rate",
}


def norm_text(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s in EMPTY_MARKERS else s


def load_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: norm_text(r.get(k, "")) for k in RESULT_FIELDS})


def blank_row() -> dict:
    return {k: "" for k in RESULT_FIELDS}


def posts_seed_rows() -> list[dict]:
    rows = []
    for p in load_csv(ROOT / POSTS):
        row = blank_row()
        row["date"] = norm_text(p.get("scheduled_date", ""))
        row["video_id"] = norm_text(p.get("video_id", ""))
        row["title"] = norm_text(p.get("caption", ""))
        rows.append(row)
    return rows


def init_files() -> None:
    rows = posts_seed_rows()
    save_csv(ROOT / TPL, rows)
    save_csv(ROOT / RES, [])
    print(f"created {TPL} ({len(rows)} rows from {POSTS})")
    print(f"reset {RES} (header only). Use --video-id ... to append.")


def canonicalize(raw: dict) -> dict:
    out = blank_row()
    for k, v in raw.items():
        key = FIELD_ALIASES.get(k, k)
        if key in RESULT_FIELDS:
            out[key] = norm_text(v)
    if not out["title"] and out["video_id"]:
        for p in load_csv(ROOT / POSTS):
            if norm_text(p.get("video_id")) == out["video_id"]:
                out["title"] = norm_text(p.get("caption", ""))
                break
    return out


def upsert(rows: list[dict], incoming: dict) -> list[dict]:
    row = canonicalize(incoming)
    vid = row["video_id"]
    if not vid:
        rows.append(row)
        return rows
    for i, existing in enumerate(rows):
        if norm_text(existing.get("video_id")) == vid:
            merged = {**existing, **{k: v for k, v in row.items() if v != ""}}
            rows[i] = merged
            return rows
    rows.append(row)
    return rows


def import_csv(path: Path) -> list[dict]:
    out = []
    for raw in load_csv(path):
        out.append(canonicalize(raw))
    return out


def apply_updates(new_rows: list[dict]) -> None:
    existing = load_csv(ROOT / RES)
    for row in new_rows:
        existing = upsert(existing, row)
    save_csv(ROOT / RES, existing)
    print(f"updated {RES} ({len(existing)} rows total)")


def build_row_from_args(ns: argparse.Namespace) -> dict:
    mapping = {
        "date": ns.date,
        "video_id": ns.video_id,
        "title": ns.title,
        "views": ns.views,
        "likes": ns.likes,
        "comments": ns.comments,
        "shares": ns.shares,
        "saves": ns.saves,
        "avg_watch_time": ns.avg_watch_time,
        "full_watch_rate": ns.full_watch_rate,
        "two_sec_retention": ns.two_sec_retention,
        "five_sec_retention": ns.five_sec_retention,
        "retention_notes": ns.retention_notes,
    }
    return {k: norm_text(v) for k, v in mapping.items() if v is not None}


def main() -> int:
    parser = argparse.ArgumentParser(description="Update results.csv with TikTok Studio insights")
    parser.add_argument("--init", action="store_true", help="Create template and empty results.csv")
    parser.add_argument("--json", metavar="FILE", help="JSON file (object or list)")
    parser.add_argument("--import-csv", metavar="FILE", dest="import_csv_path")
    parser.add_argument("--stdin", action="store_true", help="Read JSON lines from stdin")
    parser.add_argument("--video-id")
    parser.add_argument("--date")
    parser.add_argument("--title")
    parser.add_argument("--views")
    parser.add_argument("--likes")
    parser.add_argument("--comments")
    parser.add_argument("--shares")
    parser.add_argument("--saves")
    parser.add_argument("--avg-watch-time", dest="avg_watch_time")
    parser.add_argument("--full-watch-rate", dest="full_watch_rate")
    parser.add_argument("--two-sec-retention", dest="two_sec_retention")
    parser.add_argument("--five-sec-retention", dest="five_sec_retention")
    parser.add_argument("--retention-notes", dest="retention_notes")
    ns = parser.parse_args()

    if ns.init:
        init_files()
        return 0

    if not (ROOT / RES).is_file():
        save_csv(ROOT / RES, [])

    batch: list[dict] = []

    if ns.json:
        data = json.loads(Path(ns.json).read_text(encoding="utf-8"))
        if isinstance(data, list):
            batch.extend(data)
        else:
            batch.append(data)
    elif ns.import_csv_path:
        batch.extend(import_csv(Path(ns.import_csv_path)))
    elif ns.stdin:
        for line in sys.stdin:
            line = line.strip()
            if line:
                batch.append(json.loads(line))
    elif ns.video_id or ns.title or ns.views:
        batch.append(build_row_from_args(ns))
    else:
        parser.print_help()
        print("\n例: python update_results.py --video-id 7645... --views 1200 --two-sec-retention 48%")
        return 1

    try:
        apply_updates(batch)
    except (json.JSONDecodeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
