"""Update results.csv from TikTok Studio scrape (JSON) or merge registry rows.

Usage:
  python update_results.py --init
  python update_results.py --merge registry   # ensure one row per registry file
  python update_results.py metrics.json       # [{"file":"b01_s1_emo.mp4","views":100,...}, ...]
  python update_results.py --stdin            # read JSON array from stdin

JSON fields per row: file (required), posted_date, and any METRICS column from analyze_results.py.
"""
import csv
import json
import os
import sys

from analyze_results import METRICS, REG, RES, TPL, init_template, load_csv

FIELDS = ["file", "posted_date"] + METRICS


def ensure_results():
    if os.path.exists(RES):
        return load_csv(RES)
    if os.path.exists(TPL):
        rows = load_csv(TPL)
        return rows
    init_template()
    return load_csv(TPL)


def write_results(rows):
    with open(RES, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    print(f"updated {RES} ({len(rows)} rows)")


def merge_registry():
    reg = load_csv(REG)
    by_file = {r["file"]: r for r in ensure_results()}
    for r in reg:
        f = r["file"]
        if f not in by_file:
            by_file[f] = {"file": f, "posted_date": ""}
            for m in METRICS:
                by_file[f][m] = ""
    write_results(list(by_file.values()))


def apply_metrics(updates):
    by_file = {r["file"]: dict(r) for r in ensure_results()}
    n = 0
    for u in updates:
        f = u.get("file")
        if not f:
            continue
        row = by_file.setdefault(f, {"file": f, "posted_date": ""})
        for k in FIELDS:
            if k in u and u[k] not in (None, ""):
                row[k] = u[k]
        n += 1
    write_results(list(by_file.values()))
    print(f"applied metrics to {n} file(s)")


if __name__ == "__main__":
    if "--init" in sys.argv or not os.path.exists(REG):
        if not os.path.exists(REG):
            print("registry.csv がありません。")
            sys.exit(1)
        init_template()
        sys.exit(0)
    if "--merge" in sys.argv and "registry" in sys.argv:
        merge_registry()
        sys.exit(0)
    if "--stdin" in sys.argv:
        updates = json.load(sys.stdin)
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        with open(sys.argv[1], encoding="utf-8") as f:
            updates = json.load(f)
    else:
        print(__doc__)
        sys.exit(1)
    if isinstance(updates, dict):
        updates = [updates]
    apply_metrics(updates)
