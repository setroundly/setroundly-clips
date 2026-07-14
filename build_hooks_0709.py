# 0709 hooks — 縦型書き出し

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FFMPEG = "ffmpeg"
OUT = ROOT / "output" / "hooks"
TOP3 = OUT / "top3"
ALTS = OUT / "alternates"
PREV = OUT / "_preview"

WHITE = r"{\c&HFFFFFF&}"
ACCENT = r"{\c&HFFFFFF&}"  # 0709は白基調（amber強調は最小）

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,Yu Mincho,72,&H00FFFFFF,&H00FFFFFF,&H00101010,&H64000000,-1,0,0,0,100,100,1,0,1,4,2,2,48,48,280,1
Style: Hook,Yu Mincho,118,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,-1,0,0,0,100,100,2,0,1,6,4,8,24,24,0,1
Style: Scrim,Arial,1,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Bug,Yu Mincho,52,&H00FFFFFF,&H00FFFFFF,&H00101010,&H78000000,-1,0,0,0,100,100,1,0,1,2,1,2,56,56,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""


def ts(t: float) -> str:
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def acc(text: str) -> str:
    return text.replace("«", ACCENT).replace("»", WHITE)


def crop_filter(width: int, height: int, cx: int | None = None, zoom: float = 1.0) -> str:
    """Center-ish vertical crop from landscape, optional zoom (<=1.3)."""
    target_w = int(round(height * 9 / 16 / zoom))
    target_w = min(target_w, width)
    # keep even
    target_w -= target_w % 2
    if cx is None:
        x = (width - target_w) // 2
    else:
        x = max(0, min(width - target_w, cx - target_w // 2))
    x -= x % 2
    return f"crop={target_w}:{height}:{x}:0,scale=1080:1920:flags=lanczos"


CLIPS = [
    {
        "tier": "top3",
        "name": "h01_kagi2_lyric",
        "src": "ポストに鍵2.mp4",
        "song": "ポストに鍵",
        "kind": "歌詞フック",
        "start": 17.80,
        "end": 35.50,
        "width": 1920,
        "height": 1080,
        "cx": 980,
        "zoom": 1.0,
        "hook": "不倫相手は、\\N鍵をポストに返す",
        "hook_plain": "不倫相手は、鍵をポストに返す",
        "hook_ab": "鍵をポストに捨てて、帰っていった人の話。",
        "first_lyric": "ポストに鍵放り込んで",
        "captions": [
            (0.4, 4.2, "ポストに鍵放り込んで"),
            (4.2, 9.0, "あなたはあの人の\\N元へ帰って行く"),
            (9.0, 14.5, "残された部屋で\\N歌ってる"),
        ],
        "caption_post": "不倫相手は、鍵をポストに返す。 SETROUNDLY #ライブ #インディーズ",
        "reason": "寄り画・表情・歌詞の物語性が最も強く、最初の2秒で状況が伝わる。",
        "weakness": "刺激強めのフックなので、ターゲット外は即離脱の可能性。",
        "confidence": "高",
        "grade": "eq=saturation=1.05:contrast=1.04",
    },
    {
        "tier": "top3",
        "name": "h02_answer2_vocal",
        "src": "アンサー2.mp4",
        "song": "アンサー",
        "kind": "歌唱力フック",
        "start": 241.70,
        "end": 259.50,
        "width": 1920,
        "height": 1080,
        "cx": 900,
        "zoom": 1.15,
        "hook": "最後に残ったものが、\\N答えだった",
        "hook_plain": "最後に残ったものが、答えだった",
        "hook_ab": "半世紀分の旅の、答え。",
        "first_lyric": "（終盤サビ／声量ピーク）",
        "captions": [
            (0.5, 5.0, "最後に残った\\Nそれが答え"),
            (5.0, 11.0, "それでも\\N歌い続けてる"),
            (11.0, 16.0, "この声が\\N答えだった"),
        ],
        "caption_post": "最後に残ったものが、答えだった。 SETROUNDLY #ライブ #インディーズ",
        "reason": "04:02付近の表情・声量が強く、拡散型の熱量に寄せられる。",
        "weakness": "フック文が抽象的なので、歌詞字幕がないと意味が遅れやすい。",
        "confidence": "高",
        "grade": "eq=saturation=1.08:contrast=1.05:brightness=0.01",
    },
    {
        "tier": "top3",
        "name": "h03_polaris11_empathy",
        "src": "ポラリス11.mp4",
        "song": "ポラリス",
        "kind": "共感フック",
        "start": 115.80,
        "end": 133.00,
        "width": 1280,
        "height": 720,
        "cx": 640,
        "zoom": 1.0,
        "hook": "誰にも見つからなくても、\\N光っていた",
        "hook_plain": "誰にも見つからなくても、光っていた",
        "hook_ab": "見つけてもらえなくても、消えない光。",
        "first_lyric": "（光／ポラリス系フレーズ）",
        "captions": [
            (0.4, 5.5, "誰にも\\N見つからなくても"),
            (5.5, 11.0, "ひとりで\\N光っていた"),
            (11.0, 16.5, "それが\\Nポラリス"),
        ],
        "caption_post": "誰にも見つからなくても、光っていた。 SETROUNDLY #ライブ #インディーズ",
        "reason": "音の立ち上がりと寄り画のバランスがよく、深度型の置きやすい共感フック。",
        "weakness": "720p素材のため画質が1080pより落ちる。",
        "confidence": "中",
        "grade": "eq=saturation=1.06:contrast=1.05",
    },
    {
        "tier": "alternates",
        "name": "h04_senobi1_empathy",
        "src": "背伸び1.mp4",
        "song": "背伸び",
        "kind": "共感フック",
        "start": 164.50,
        "end": 184.00,
        "width": 1920,
        "height": 1080,
        "cx": 960,
        "zoom": 1.2,
        "hook": "昔の自分に、\\N会いに行く歌",
        "hook_plain": "昔の自分に、会いに行く歌",
        "hook_ab": "背伸びしてた頃の、自分へ。",
        "first_lyric": "（終盤・歌い切り）",
        "captions": [
            (0.4, 5.0, "昔の自分に\\N会いに行く"),
            (5.0, 11.0, "背伸びしてた\\Nあの頃へ"),
            (11.0, 17.5, "まだ間に合う\\N気がして"),
        ],
        "caption_post": "昔の自分に、会いに行く歌。 SETROUNDLY #ライブ #インディーズ",
        "reason": "02:46付近の表情が強く、共感×歌唱の次点として有効。",
        "weakness": "0606「背伸びしてた頃の歌。」とトーンが近いので、同週並びは避ける。",
        "confidence": "中",
        "grade": "eq=saturation=1.05:contrast=1.04",
    },
    {
        "tier": "alternates",
        "name": "h05_kimari1_vocal",
        "src": "決まり事1.mp4",
        "song": "決まり事",
        "kind": "歌唱力フック",
        "start": 157.80,
        "end": 177.50,
        "width": 1920,
        "height": 1080,
        "cx": 1180,
        "zoom": 1.25,
        "hook": "守れなかった決まり事ばかり\\N増えた",
        "hook_plain": "守れなかった決まり事ばかり増えた",
        "hook_ab": "決まり事が増えるほど、本音が出る。",
        "first_lyric": "（ラスト付近の高揚）",
        "captions": [
            (0.4, 5.5, "守れなかった\\N決まり事"),
            (5.5, 11.5, "ばっかり\\N増えていく"),
            (11.5, 17.5, "それでも\\N歌ってる"),
        ],
        "caption_post": "守れなかった決まり事ばかり増えた。 SETROUNDLY #ライブ #インディーズ",
        "reason": "ラスト高揚の歌唱力フック。アンサー2の代替拡散枠。",
        "weakness": "横顔寄りなので顔が画面端に寄りやすい。クロップ依存。",
        "confidence": "中",
        "grade": "eq=saturation=1.07:contrast=1.05",
    },
]


def write_ass(spec: dict, duration: float, ass_path: Path) -> None:
    lines = []
    hook_end = min(4.2, duration - 0.5)
    scrim = (
        r"{\p1\an7\pos(0,0)\1c&H000000&\1a&HA0&\bord0\shad0}"
        "m 0 0 l 1080 0 1080 520 0 520{\\p0}"
    )
    lines.append(f"Dialogue: 1,{ts(0)},{ts(hook_end)},Scrim,,0,0,,{scrim}")
    lines.append(
        f"Dialogue: 2,{ts(0)},{ts(hook_end)},Hook,,0,0,,"
        f"{{\\an8\\pos(540,220)}}{acc(spec['hook'])}"
    )
    for a, b, txt in spec.get("captions", []):
        A = max(hook_end + 0.1, a)
        B = min(duration - 1.6, b)
        if B - A < 0.3:
            continue
        lines.append(f"Dialogue: 0,{ts(A)},{ts(B)},Lyric,,0,0,,{acc(txt)}")
    bug_a = max(0.0, duration - 1.8)
    lines.append(
        f"Dialogue: 2,{ts(bug_a)},{ts(duration)},Bug,,0,0,,"
        f"{spec['song']} / SETROUNDLY"
    )
    ass_path.write_text(HEAD + "\n".join(lines) + "\n", encoding="utf-8")


def build_one(spec: dict) -> Path:
    src = ROOT / spec["src"]
    if not src.exists():
        raise FileNotFoundError(src)
    dest_dir = TOP3 if spec["tier"] == "top3" else ALTS
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / f"{spec['name']}.mp4"
    ass = OUT / f"{spec['name']}.ass"
    duration = spec["end"] - spec["start"]
    write_ass(spec, duration, ass)

    crop = crop_filter(spec["width"], spec["height"], spec.get("cx"), spec.get("zoom", 1.0))
    grade = spec.get("grade", "")
    grade_s = f",{grade}" if grade else ""
    # Windows path for ass filter: escape colon/backslash
    ass_esc = str(ass).replace("\\", "/").replace(":", "\\:")

    vf = (
        f"{crop}{grade_s},fps=30,setsar=1,"
        f"ass='{ass_esc}'"
    )
    af = (
        f"atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=0.02,afade=t=out:st={duration-0.08:.3f}:d=0.08,"
        f"loudnorm=I=-14:TP=-1.0:LRA=11"
    )
    cmd = [
        FFMPEG, "-y",
        "-ss", f"{spec['start']:.3f}",
        "-i", str(src),
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out),
    ]
    print(f"=== {spec['name']}  ({duration:.1f}s) ===", flush=True)
    subprocess.run(cmd, check=True)
    return out


def write_reports(built: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    top = [c for c in built if c["tier"] == "top3"]
    lines = [
        "# 0709 hooks report",
        "",
        "## 最有力3本（先出し）",
        "",
        "| # | 型 | ファイル | 開始 | 終了 | 尺 | 大字 | 自信 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, c in enumerate(top, 1):
        lines.append(
            f"| {i} | {c['kind']} | {c['src']} | {c['start']:.2f} | {c['end']:.2f} | "
            f"{c['end']-c['start']:.1f}s | {c['hook_plain']} | {c['confidence']} |"
        )
    lines += [
        "",
        "### 選定理由（要約）",
        "",
        "1. **ポストに鍵2** — 歌詞の物語性が一発で伝わる（深度寄り）。",
        "2. **アンサー2** — 終盤の声量・表情で拡散枠。",
        "3. **ポラリス11** — 共感フック。歌詞/歌唱と型を分散。",
        "",
        "---",
        "",
    ]
    for c in built:
        d = c["end"] - c["start"]
        lines += [
            f"## {c['name']}（{c['tier']}）",
            "",
            f"- 元ファイル: `{c['src']}`",
            f"- 開始〜終了: `{c['start']:.2f}` — `{c['end']:.2f}`（{d:.1f}s）",
            f"- 型: {c['kind']}",
            f"- 冒頭大字: {c['hook_plain']}",
            f"- 最初の歌詞: {c['first_lyric']}",
            f"- キャプション案: {c['caption_post']}",
            f"- 採用理由: {c['reason']}",
            f"- 想定弱点: {c['weakness']}",
            f"- A/B別テロップ: {c['hook_ab']}",
            f"- 自信: {c['confidence']}",
            "",
        ]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = []
    for c in built:
        payload.append(
            {
                "file": c["name"] + ".mp4",
                "tier": c["tier"],
                "src": c["src"],
                "song": c["song"],
                "kind": c["kind"],
                "start": c["start"],
                "end": c["end"],
                "duration": round(c["end"] - c["start"], 2),
                "hook": c["hook_plain"],
                "hook_ab": c["hook_ab"],
                "first_lyric": c["first_lyric"],
                "caption": c["caption_post"],
                "reason": c["reason"],
                "weakness": c["weakness"],
                "confidence": c["confidence"],
            }
        )
    (OUT / "candidates.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    TOP3.mkdir(parents=True, exist_ok=True)
    ALTS.mkdir(parents=True, exist_ok=True)
    write_reports(CLIPS)
    print("Wrote report.md + candidates.json", flush=True)
    for spec in CLIPS:
        build_one(spec)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
