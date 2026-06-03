"""Generate registry.csv: maps each produced video to its editing parameters.
This is the backbone of the data-driven loop (join with results to find winners)."""
import csv, re

import build_patterns, build_batch, build_mc
from build_patterns import GOLD, CREAM, AMBER

ACCENT_NAME = {GOLD: "gold", CREAM: "cream", AMBER: "amber"}

# ライブ区間コード (section) → 曲名（TikTok 仕訳・分析用）
SECTION_TO_SONG = {
    "HH_1stChorus": "ハニーハニー",
    "HH_Misekake": "ハニーハニー",
    "HH_2ndChorus_hari": "ハニーハニー",
    "HH_Aitai": "ハニーハニー",
    "CO2_utauyo": "CO2",
    "LastSong_kasa": "透明な傘",
    "MC_guitar": "MC",
    "MC_blue": "MC",
    "MC_bike/nostalgia": "MC",
}


def song_of(section: str) -> str:
    if section in SECTION_TO_SONG:
        return SECTION_TO_SONG[section]
    if section.startswith("other_"):
        return "（未分類）"
    return section


def style_of(grade):
    if "vignette" in grade: return "emo"
    if "gamma" in grade:    return "song"
    return "viral"

def section_of(seg_start):
    s = seg_start
    if 70 <= s < 110:   return "HH_1stChorus"
    if 122 <= s < 145:  return "HH_Misekake"
    if 190 <= s < 216:  return "HH_2ndChorus_hari"
    if 216 <= s < 250:  return "HH_Aitai"
    if 770 <= s < 805:  return "CO2_utauyo"
    if 1380 <= s < 1465: return "MC_bike/nostalgia"
    if 280 <= s < 330:  return "MC_blue"
    if 880 <= s < 920:  return "MC_guitar"
    if 1620 <= s < 1645: return "LastSong_kasa"
    return f"other_{int(s)}"

def clean(t):
    t = t.replace("\\N", " ").replace("«", "").replace("»", "")
    t = re.sub(r"\{[^}]*\}", "", t)
    return t.strip()

rows = []
for mod in (build_patterns, build_batch, build_mc):
    for sp in mod.VIDEOS:
        seg0 = sp["segments"][0][0]
        intro = sp.get("intro")
        hook = clean(intro[1]) if intro else (clean(sp["hooks"][0][2]) if sp.get("hooks") else "")
        sec = section_of(seg0)
        rows.append({
            "file": sp["name"] + ".mp4",
            "song": song_of(sec),
            "section": sec,
            "style": style_of(sp.get("grade", "")),
            "intro_black": "yes" if intro else "no",
            "accent": ACCENT_NAME.get(sp.get("accent", ""), "?"),
            "n_cuts": len(sp["segments"]),
            "hook": hook,
        })

rows.sort(key=lambda r: (r["song"], r["file"]))

FIELDS = ["file", "song", "section", "style", "intro_black", "accent", "n_cuts", "hook"]
with open("registry.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print(f"wrote registry.csv ({len(rows)} videos)")

REPORTS = __import__("pathlib").Path(__file__).resolve().parent / "reports"
REPORTS.mkdir(exist_ok=True)
by_song = {}
for r in rows:
    by_song.setdefault(r["song"], []).append(r)
lines = ["# 動画一覧（曲名仕訳）\n", "registry.csv の `song` 列。`python make_registry.py` で再生成。\n"]
for song in sorted(by_song.keys(), key=lambda s: (s == "MC", s)):
    lines.append(f"\n## {song}\n")
    lines.append("| file | section | style | intro | hook |")
    lines.append("|------|---------|-------|-------|------|")
    for r in by_song[song]:
        hook = r["hook"].replace("|", "\\|")[:40]
        lines.append(
            f"| {r['file']} | {r['section']} | {r['style']} | {r['intro_black']} | {hook} |"
        )
(REPORTS / "videos_by_song.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {REPORTS / 'videos_by_song.md'}")

for r in rows:
    print(f"  {r['song']:8} {r['file']:24} {r['section']:20} {r['style']:6} intro={r['intro_black']:3} | {r['hook'][:36]}")
