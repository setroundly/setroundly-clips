"""Data-driven loop: join registry.csv (editing params) with results.csv (TikTok insights)
and surface which section / style / hook / accent / intro wins, then recommend the next batch.

Usage:
  python analyze_results.py --init
  python analyze_results.py
  python analyze_results.py --json
  python analyze_results.py --report reports/2026-06-06_weekly.md
"""
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date

REG = "registry.csv"
TPL = "results_template.csv"
RES = "results.csv"

METRICS = [
    "views", "sec2_rate", "avg_watch_s", "full_watch_rate",
    "likes", "comments", "saves", "shares", "followers_gained",
]

WEIGHTS = {
    "full_watch_rate": 0.45,
    "sec2_rate": 0.20,
    "save_rate": 0.20,
    "comment_rate": 0.10,
    "avg_watch_s": 0.05,
}

DIMS = ["section", "style", "accent", "intro_black"]


def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def init_template():
    reg = load_csv(REG)
    with open(TPL, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "posted_date"] + METRICS)
        for r in reg:
            w.writerow([r["file"], ""] + [""] * len(METRICS))
    print(f"created {TPL} ({len(reg)} rows). 数字を入れて results.csv に保存してください。")


def fnum(v):
    try:
        return float(str(v).replace("%", "").replace(",", "").strip())
    except Exception:
        return None


def minmax(vals):
    xs = [v for v in vals if v is not None]
    if not xs:
        return lambda x: 0.0
    lo, hi = min(xs), max(xs)
    if hi == lo:
        return lambda x: 0.5 if x is not None else 0.0
    return lambda x: (x - lo) / (hi - lo) if x is not None else 0.0


def rank_by(rows, dim):
    g = defaultdict(list)
    for r in rows:
        g[r[dim]].append(r["score"])
    out = [(k, round(sum(v) / len(v), 1), len(v)) for k, v in g.items()]
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def compute_analysis():
    """Return analysis dict, or None if no usable rows."""
    if not os.path.exists(REG):
        raise FileNotFoundError("registry.csv がありません。先に python make_registry.py")
    if not os.path.exists(RES):
        return None

    reg = {r["file"]: r for r in load_csv(REG)}
    res = load_csv(RES)
    rows = []
    pending = []
    for r in res:
        f = r["file"]
        if f not in reg:
            continue
        m = {k: fnum(r.get(k, "")) for k in METRICS}
        if m["views"] is None or m["views"] == 0:
            pending.append(f)
            continue
        m["save_rate"] = (m["saves"] / m["views"] * 100) if m["saves"] is not None else None
        m["comment_rate"] = (m["comments"] / m["views"] * 100) if m["comments"] is not None else None
        rows.append({**reg[f], **m, "file": f, "posted_date": r.get("posted_date", "")})

    if not rows:
        return {"rows": [], "pending": pending, "rankings": {}, "recommendation": None}

    norms = {}
    for key in ["full_watch_rate", "sec2_rate", "save_rate", "comment_rate", "avg_watch_s"]:
        norms[key] = minmax([row.get(key) for row in rows])
    for row in rows:
        row["score"] = round(sum(WEIGHTS[k] * norms[k](row.get(k)) for k in WEIGHTS) * 100, 1)

    rows.sort(key=lambda r: r["score"], reverse=True)
    rankings = {dim: rank_by(rows, dim) for dim in DIMS}
    rec = {
        "section": rankings["section"][0][0],
        "style": rankings["style"][0][0],
        "accent": rankings["accent"][0][0],
        "intro_black": rankings["intro_black"][0][0],
        "top_hooks": [{"hook": r["hook"], "file": r["file"]} for r in rows[:3]],
        "bottom_files": [r["file"] for r in rows[-3:]],
    }
    return {
        "rows": rows,
        "pending": pending,
        "rankings": rankings,
        "recommendation": rec,
    }


def print_analysis(data):
    rows = data["rows"]
    if not rows:
        print("results.csv に有効な行がありません（views を入れてください）。")
        if data.get("pending"):
            print(f"  公開待ち（views=0）: {len(data['pending'])} 件")
        return

    print("\n=== 個別ランキング（合成スコア／維持率重視）===")
    for r in rows:
        save = r.get("save_rate")
        save_s = f"{round(save, 1)}%" if save is not None else "-"
        print(
            f"  {r['score']:5.1f}  {r['file']:22} {r['section']:18} {r['style']:5} "
            f"intro={r['intro_black']:3} {r['accent']:5} | full={r.get('full_watch_rate')}% save={save_s}"
        )

    for dim in DIMS:
        print(f"\n=== {dim} 別 平均スコア ===")
        for k, avg, n in data["rankings"][dim]:
            print(f"  {avg:5.1f}  {k}  (n={n})")

    rec = data["recommendation"]
    print("\n=== 次バッチの推奨配合 ===")
    print(
        f"  主軸：区間={rec['section']} / スタイル={rec['style']} / "
        f"アクセント={rec['accent']} / 黒イントロ={rec['intro_black']}"
    )
    print("  → この組合せを多めに。下位の区間/スタイルは本数を減らすか、勝ちフックで作り直し。")
    print("  勝ちフック上位3：")
    for h in rec["top_hooks"]:
        print(f"    ・{h['hook']}  ({h['file']})")


def write_report(data, path, competitor_notes="", next_edit_notes=""):
    """Write weekly markdown report (analysis section; agent fills competitor/edit)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    rows = data["rows"]
    rec = data.get("recommendation")

    lines = [
        f"# SETROUNDLY 週次レポート ({date.today().isoformat()})",
        "",
        "## 1. KPIサマリー",
        "",
    ]
    if not rows:
        lines.append("_今週は公開済みで views>0 の投稿がまだありません。TikTok Studio から数値を取得してください。_")
    else:
        total_views = sum(r.get("views") or 0 for r in rows)
        avg_full = sum(r.get("full_watch_rate") or 0 for r in rows) / len(rows)
        lines.append(f"- 分析対象: **{len(rows)}** 本")
        lines.append(f"- 合計 views: **{int(total_views):,}**")
        lines.append(f"- 平均フル視聴率: **{avg_full:.1f}%**")
        lines.append("")
        lines.append("| score | file | section | style | full% | save% |")
        lines.append("|------:|------|---------|-------|------:|------:|")
        for r in rows:
            save = r.get("save_rate")
            save_s = f"{save:.1f}" if save is not None else "-"
            full = r.get("full_watch_rate")
            full_s = f"{full:.1f}" if full is not None else "-"
            lines.append(
                f"| {r['score']} | {r['file']} | {r['section']} | {r['style']} | {full_s} | {save_s} |"
            )

    lines.extend(["", "## 2. 勝ち / 負けパターン（自社）", ""])
    if rec:
        for dim in DIMS:
            top = data["rankings"][dim][0]
            bot = data["rankings"][dim][-1]
            lines.append(f"- **{dim}** 勝ち: `{top[0]}` (avg {top[1]}, n={top[2]}) / 負け: `{bot[0]}` (avg {bot[1]})")
        lines.append("")
        lines.append("### 次バッチ推奨")
        lines.append(
            f"- 区間 `{rec['section']}` / スタイル `{rec['style']}` / "
            f"アクセント `{rec['accent']}` / 黒イントロ `{rec['intro_black']}` を厚く"
        )
        lines.append("- 勝ちフック:")
        for h in rec["top_hooks"]:
            lines.append(f"  - {h['hook']} (`{h['file']}`)")
        if rec["bottom_files"]:
            lines.append("- 薄くする候補:")
            for f in rec["bottom_files"]:
                lines.append(f"  - `{f}`")
    else:
        lines.append("_分析データなし_")

    lines.extend(["", "## 3. 競合から学んだ3点", ""])
    lines.append(competitor_notes.strip() or "_（Automation が TikTok 検索後に追記）_")

    lines.extend(["", "## 4. 来週の編集方針", ""])
    lines.append(next_edit_notes.strip() or "_（勝ち型 + 競合メモを反映して追記）_")

    lines.extend(["", "## 5. 今週生成した動画", ""])
    lines.append("_（`build_batch.py` / `build_mc.py` 実行後にファイル名を追記）_")

    if data.get("pending"):
        lines.extend(["", "## 付記: 公開待ち", ""])
        for f in data["pending"]:
            lines.append(f"- `{f}`")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    if not os.path.exists(REG):
        print("registry.csv がありません。先に python make_registry.py を実行してください。")
        sys.exit(1)
    if "--init" in sys.argv:
        init_template()
        sys.exit(0)

    if not os.path.exists(RES):
        if not os.path.exists(TPL):
            init_template()
        print(f"\n{RES} が見つかりません。TikTok Studio から数値を取得し update_results.py で更新してください。")
        sys.exit(2)

    data = compute_analysis()
    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        sys.exit(0 if data["rows"] else 2)

    print_analysis(data)
    for i, arg in enumerate(sys.argv):
        if arg == "--report" and i + 1 < len(sys.argv):
            write_report(data, sys.argv[i + 1])
    sys.exit(0 if data["rows"] else 2)
