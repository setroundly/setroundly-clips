"""Data-driven loop: join registry.csv (editing params) with results.csv (TikTok insights)
and surface which section / style / hook / accent / intro wins, then recommend the next batch.

Usage:
  1) python analyze_results.py --init     -> creates results_template.csv (file列入り)
  2) results_template.csv に数字を入れて results.csv にリネーム
  3) python analyze_results.py            -> 分析＋次バッチ推奨
"""
import csv, os, sys
from collections import defaultdict

REG = "registry.csv"
TPL = "results_template.csv"
RES = "results.csv"

# KPI columns the user fills from TikTok insights
METRICS = ["views", "sec2_rate", "avg_watch_s", "full_watch_rate",
           "likes", "comments", "saves", "shares", "followers_gained"]

# 視聴維持率を最優先にした合成スコアの重み
WEIGHTS = {"full_watch_rate": 0.45, "sec2_rate": 0.20,
           "save_rate": 0.20, "comment_rate": 0.10, "avg_watch_s": 0.05}


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


def analyze():
    reg = {r["file"]: r for r in load_csv(REG)}
    res = load_csv(RES)
    rows = []
    for r in res:
        f = r["file"]
        if f not in reg:
            continue
        m = {k: fnum(r.get(k, "")) for k in METRICS}
        if m["views"] is None or m["views"] == 0:
            continue
        m["save_rate"] = (m["saves"] / m["views"] * 100) if m["saves"] is not None else None
        m["comment_rate"] = (m["comments"] / m["views"] * 100) if m["comments"] is not None else None
        rows.append({**reg[f], **m, "file": f})
    if not rows:
        print("results.csv に有効な行がありません（views を入れてください）。")
        return

    # normalize each metric used in score, then weighted composite
    norms = {}
    for key in ["full_watch_rate", "sec2_rate", "save_rate", "comment_rate", "avg_watch_s"]:
        norms[key] = minmax([row.get(key) for row in rows])
    for row in rows:
        row["score"] = round(sum(WEIGHTS[k] * norms[k](row.get(k)) for k in WEIGHTS) * 100, 1)

    rows.sort(key=lambda r: r["score"], reverse=True)
    print("\n=== 個別ランキング（合成スコア／維持率重視）===")
    for r in rows:
        print(f"  {r['score']:5.1f}  {r['file']:22} {r['section']:18} {r['style']:5} "
              f"intro={r['intro_black']:3} {r['accent']:5} | full={r.get('full_watch_rate')}% save={r.get('save_rate') and round(r['save_rate'],1)}%")

    def rank_by(dim):
        g = defaultdict(list)
        for r in rows:
            g[r[dim]].append(r["score"])
        out = [(k, round(sum(v) / len(v), 1), len(v)) for k, v in g.items()]
        out.sort(key=lambda x: x[1], reverse=True)
        return out

    for dim in ["section", "style", "accent", "intro_black"]:
        print(f"\n=== {dim} 別 平均スコア ===")
        for k, avg, n in rank_by(dim):
            print(f"  {avg:5.1f}  {k}  (n={n})")

    # recommend next batch
    top_section = rank_by("section")[0][0]
    top_style = rank_by("style")[0][0]
    top_accent = rank_by("accent")[0][0]
    top_intro = rank_by("intro_black")[0][0]
    print("\n=== 次バッチの推奨配合 ===")
    print(f"  主軸：区間={top_section} / スタイル={top_style} / アクセント={top_accent} / 黒イントロ={top_intro}")
    print(f"  → この組合せを多めに。下位の区間/スタイルは本数を減らすか、勝ちフックで作り直し。")
    print(f"  勝ちフック上位3：")
    for r in rows[:3]:
        print(f"    ・{r['hook']}  ({r['file']})")


if __name__ == "__main__":
    if not os.path.exists(REG):
        print("registry.csv がありません。先に python make_registry.py を実行してください。")
        sys.exit(1)
    if "--init" in sys.argv:
        init_template()
    elif os.path.exists(RES):
        analyze()
    else:
        if not os.path.exists(TPL):
            init_template()
        print(f"\n{RES} が見つかりません。{TPL} に数字を入れ、results.csv にリネームしてから再実行してください。")
