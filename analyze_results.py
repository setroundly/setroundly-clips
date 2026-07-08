"""Join results.csv (TikTok insights) with registry.csv (editing params) and recommend edits.

Usage:
  python analyze_results.py --init     -> results_template.csv from tiktok_posts.csv
  python update_results.py ...         -> fill results.csv
  python analyze_results.py            -> 分析（維持率・完走・編集パラメータ）
"""
from __future__ import annotations

import csv
import io
import os
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

from results_schema import POSTS, REG, RES, RESULT_FIELDS, TPL

REPORTS = Path(__file__).resolve().parent / "reports"

# 数値列（% や秒も fnum で吸収）
METRICS = [
    "views", "likes", "comments", "shares", "saves",
    "avg_watch_time", "full_watch_rate", "two_sec_retention", "five_sec_retention",
]

# 視聴維持を最優先（週次 KPI と同じ思想）
WEIGHTS = {
    "full_watch_rate": 0.30,
    "two_sec_retention": 0.20,
    "five_sec_retention": 0.15,
    "save_rate": 0.15,
    "comment_rate": 0.10,
    "avg_watch_time": 0.10,
}


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def init_template():
    from update_results import posts_seed_rows, save_csv
    from pathlib import Path

    rows = posts_seed_rows()
    save_csv(Path(TPL), rows)
    print(f"created {TPL} ({len(rows)} rows). {RES} は update_results.py で更新してください。")


def fnum(v):
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "取得不可", "N/A", "n/a", "-", "—", "不明"):
        return None
    try:
        return float(s.replace("%", "").replace(",", "").replace("秒", "").strip())
    except ValueError:
        return None


def minmax(vals):
    xs = [v for v in vals if v is not None]
    if not xs:
        return lambda x: 0.0
    lo, hi = min(xs), max(xs)
    if hi == lo:
        return lambda x: 0.5 if x is not None else 0.0
    return lambda x: (x - lo) / (hi - lo) if x is not None else 0.0


def posts_index() -> dict[str, dict]:
    idx = {}
    for p in load_csv(POSTS):
        vid = str(p.get("video_id", "")).strip()
        if vid:
            idx[vid] = p
    return idx


def resolve_registry_file(result_row: dict, posts: dict[str, dict]) -> str | None:
    vid = str(result_row.get("video_id", "")).strip()
    if vid and vid in posts:
        rf = str(posts[vid].get("registry_file", "")).strip()
        if rf:
            return rf if rf.endswith(".mp4") else rf + ".mp4"
    title = str(result_row.get("title", "")).strip()
    if title:
        for p in posts.values():
            cap = str(p.get("caption", "")).strip()
            if cap and (cap == title or cap in title or title in cap):
                rf = str(p.get("registry_file", "")).strip()
                if rf:
                    return rf if rf.endswith(".mp4") else rf + ".mp4"
    return None


def retention_status(row: dict) -> str:
    t2 = fnum(row.get("two_sec_retention"))
    t5 = fnum(row.get("five_sec_retention"))
    full = fnum(row.get("full_watch_rate"))
    if t2 is not None and t2 < 35:
        return "冒頭離脱が強い（2秒維持が低い）"
    if t5 is not None and t2 is not None and t5 < t2 * 0.7:
        return "2秒は通るが5秒で落ちる（中盤が弱い）"
    if full is not None and full >= 12:
        return "完走率が高い（最後まで見られている）"
    if full is not None and full < 5:
        return "完走率が低い（尺の後半で離脱）"
    return "標準的な維持"


def analyze():
    if not os.path.exists(REG):
        print("registry.csv がありません。先に python make_registry.py を実行してください。")
        return

    reg = {r["file"]: r for r in load_csv(REG)}
    posts = posts_index()
    res = load_csv(RES)
    rows = []
    skipped = []

    for r in res:
        views = fnum(r.get("views"))
        if views is None or views == 0:
            notes = str(r.get("retention_notes", "")).strip()
            if notes or str(r.get("video_id", "")).strip():
                skipped.append(r)
            continue

        reg_file = resolve_registry_file(r, posts)
        base = dict(r)
        if reg_file and reg_file in reg:
            base = {**reg[reg_file], **base, "file": reg_file}
        else:
            base["file"] = reg_file or ""
            base.setdefault("song", "（未紐付け）")
            base.setdefault("section", "—")
            base.setdefault("style", "—")
            base.setdefault("intro_black", "—")
            base.setdefault("accent", "—")
            base.setdefault("hook", str(r.get("title", ""))[:40])

        m = {k: fnum(r.get(k, "")) for k in METRICS}
        m["save_rate"] = (m["saves"] / views * 100) if m["saves"] is not None else None
        m["comment_rate"] = (m["comments"] / views * 100) if m["comments"] is not None else None
        base.update(m)
        base["retention_label"] = retention_status(base)
        rows.append(base)

    if skipped:
        print(f"\n=== スキップ（views なし / 公開待ち）: {len(skipped)} 件 ===")
        for s in skipped[:8]:
            print(f"  {s.get('video_id', '?'):20} {s.get('title', '')[:30]}")

    if not rows:
        print("results.csv に分析可能な行がありません（views を入れてください）。")
        return

    score_keys = [
        "full_watch_rate", "two_sec_retention", "five_sec_retention",
        "save_rate", "comment_rate", "avg_watch_time",
    ]
    norms = {k: minmax([row.get(k) for row in rows]) for k in score_keys}
    for row in rows:
        row["score"] = round(sum(WEIGHTS[k] * norms[k](row.get(k)) for k in WEIGHTS) * 100, 1)

    rows.sort(key=lambda r: r["score"], reverse=True)

    print("\n=== 個別ランキング（維持率・完走・保存を重視）===")
    for r in rows:
        song = r.get("song", "?")
        fname = r.get("file") or r.get("video_id", "?")
        print(
            f"  {r['score']:5.1f}  {fname:22} {song:8} "
            f"2s={r.get('two_sec_retention') or '—':>5} 5s={r.get('five_sec_retention') or '—':>5} "
            f"full={r.get('full_watch_rate') or '—':>5} avg={r.get('avg_watch_time') or '—':>5}s | "
            f"{r['retention_label']}"
        )

    def rank_by(dim):
        g = defaultdict(list)
        for r in rows:
            if r.get(dim) and r[dim] != "—":
                g[r[dim]].append(r["score"])
        out = [(k, round(sum(v) / len(v), 1), len(v)) for k, v in g.items()]
        out.sort(key=lambda x: x[1], reverse=True)
        return out

    for dim in ["song", "section", "style", "intro_black", "accent"]:
        ranked = rank_by(dim)
        if not ranked:
            continue
        print(f"\n=== {dim} 別 平均スコア ===")
        for k, avg, n in ranked:
            print(f"  {avg:5.1f}  {k}  (n={n})")

    # 維持率サマリー
    t2_vals = [r.get("two_sec_retention") for r in rows if r.get("two_sec_retention") is not None]
    t5_vals = [r.get("five_sec_retention") for r in rows if r.get("five_sec_retention") is not None]
    full_vals = [r.get("full_watch_rate") for r in rows if r.get("full_watch_rate") is not None]
    print("\n=== 視聴維持サマリー ===")
    if t2_vals:
        print(f"  2秒維持率 平均 {sum(t2_vals)/len(t2_vals):.1f}%  → 冒頭フックの強さの目安")
    else:
        print("  2秒維持率: 取得不可の投稿あり（retention_notes を確認）")
    if t5_vals:
        print(f"  5秒維持率 平均 {sum(t5_vals)/len(t5_vals):.1f}%  → フック直後の展開の目安")
    if full_vals:
        print(f"  完走率 平均 {sum(full_vals)/len(full_vals):.1f}%  → 尺全体・後半の目安")

    # 伸びた動画の共通点
    top, bottom = rows[: max(1, len(rows) // 3)], rows[-max(1, len(rows) // 3):]
    print("\n=== 伸びた動画の共通点（上位群）===")
    for label, key in [("曲", "song"), ("スタイル", "style"), ("黒イントロ", "intro_black"), ("アクセント", "accent")]:
        vals = [r.get(key) for r in top if r.get(key) and r[key] != "—"]
        if vals:
            common = max(set(vals), key=vals.count)
            print(f"  ・{label}は「{common}」が多い（{vals.count(common)}/{len(vals)} 本）")
    hooks = [r.get("hook", "") for r in top if r.get("hook")]
    if hooks:
        print(f"  ・勝ちフック例: 「{hooks[0][:50]}」")

    low_t2 = [r for r in rows if r.get("two_sec_retention") is not None and r["two_sec_retention"] < 40]
    high_full = [r for r in rows if r.get("full_watch_rate") is not None and r["full_watch_rate"] >= 10]
    if low_t2:
        print("\n=== 冒頭で離脱されやすい投稿（2秒維持 < 40%）===")
        for r in low_t2[:5]:
            print(f"  ・{r.get('file') or r.get('title', '')[:24]} — 2s={r['two_sec_retention']}% hook={r.get('hook', '')[:28]}")
    if high_full:
        print("\n=== 最後まで見られやすい投稿（完走率 >= 10%）===")
        for r in sorted(high_full, key=lambda x: x.get("full_watch_rate", 0), reverse=True)[:5]:
            print(f"  ・{r.get('file') or r.get('title', '')[:24]} — full={r['full_watch_rate']}% style={r.get('style')}")

    # 改善案
    print("\n=== 改善案（次週の編集）===")
    if low_t2:
        intro_yes = sum(1 for r in low_t2 if r.get("intro_black") == "yes")
        if intro_yes >= len(low_t2) // 2:
            print("  ・冒頭離脱が多い → 黒イントロは短くするか、overlay 型（歌と同時にフック）を厚くする")
        else:
            print("  ・冒頭離脱が多い → フック文言の改行・強調語（«»）・最初の1秒の無音/暗幕を見直す")
    if t5_vals and t2_vals and sum(t5_vals) / len(t5_vals) < sum(t2_vals) / len(t2_vals) * 0.75:
        print("  ・2秒は通るが5秒で落ちる → フック後すぐ歌詞/展開を入れる。MC 寄りカットは短く")
    if full_vals and sum(full_vals) / len(full_vals) < 8:
        print("  ・完走率が低い → 尺を短く（15秒前後）、サビ直結 or 1区間のみに絞る")
    ranked_style = rank_by("style")
    if ranked_style:
        print(f"  ・スタイルは「{ranked_style[0][0]}」寄りを増やす（平均スコア {ranked_style[0][1]}）")
    ranked_song = rank_by("song")
    if ranked_song:
        print(f"  ・曲は「{ranked_song[0][0]}」の区間を厚く（平均スコア {ranked_song[0][1]}）")
    print("  ・維持率が Studio で取れなかった行は retention_notes に「取得不可」と入れ、分析からは views のみ参照")

    top_section = rank_by("section")
    top_style = rank_by("style")
    top_accent = rank_by("accent")
    top_intro = rank_by("intro_black")
    if top_section and top_style and top_accent and top_intro:
        print("\n=== 次バッチの推奨配合 ===")
        print(
            f"  主軸：曲={rank_by('song')[0][0] if rank_by('song') else '?'} / "
            f"区間={top_section[0][0]} / スタイル={top_style[0][0]} / "
            f"アクセント={top_accent[0][0]} / 黒イントロ={top_intro[0][0]}"
        )
    print("  勝ちフック上位3：")
    for r in rows[:3]:
        print(f"    ・{r.get('hook', r.get('title', ''))}  ({r.get('file') or r.get('video_id')})")


if __name__ == "__main__":
    if "--init" in sys.argv:
        if not os.path.exists(REG):
            print("registry.csv がありません。先に python make_registry.py を実行してください。")
            sys.exit(1)
        init_template()
    elif os.path.exists(RES):
        if "--report" in sys.argv:
            buf = io.StringIO()
            with redirect_stdout(buf):
                analyze()
            text = buf.getvalue()
            print(text, end="")
            REPORTS.mkdir(exist_ok=True)
            out = REPORTS / f"{date.today().isoformat()}_analysis.txt"
            out.write_text(text, encoding="utf-8")
            print(f"\n（レポート保存: {out}）")
        else:
            analyze()
    else:
        if not os.path.exists(TPL):
            init_template()
        print(f"\n{RES} が見つかりません。python update_results.py --init のあと数値を追記してください。")
