import subprocess

from config import FFMPEG, SRC

SRC = str(SRC)
FFMPEG = str(FFMPEG)
WHITE = r"{\\c&HFFFFFF&}"

def ts(t):
    if t < 0: t = 0
    h = int(t//3600); m = int((t%3600)//60); s = t%60
    return f"{h}:{m:02d}:{s:05.2f}"

# ASS styles tuned for a "music-media" look: bold Yu Gothic, thin outline + soft shadow,
# translucent strip behind the hook line, slight letter-spacing.
HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,Yu Gothic UI,98,&H00FFFFFF,&H00FFFFFF,&H00141414,&HB4000000,-1,0,0,0,100,100,1,0,1,4,2,2,40,40,230,1
Style: Hook,Yu Gothic UI,150,&H00FFFFFF,&H00FFFFFF,&H00141414,&H00000000,-1,0,0,0,100,100,2,0,1,6,5,5,12,12,0,1
Style: Scrim,Arial,1,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Bug,Yu Gothic UI,58,&H00FFFFFF,&H00FFFFFF,&H00141414,&H78000000,-1,0,0,0,100,100,2,0,1,2,1,2,60,60,130,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""

def build(spec):
    name = spec["name"]
    accent = spec["accent"]              # e.g. r"{\c&H4DCCFF&}"
    def acc(t):
        return t.replace("«", accent).replace("»", WHITE)

    seek = max(0.0, min(s for s, e in spec["segments"]) - 2.0)
    segments = [(s - seek, e - seek) for s, e in spec["segments"]]
    caps = [(a - seek, b - seek, t) for a, b, t in spec.get("captions", [])]
    offsets = []; acc0 = 0.0
    for s, e in segments:
        offsets.append(acc0); acc0 += e - s
    total = acc0

    ass = name + ".ass"
    intro = spec.get("intro")            # (duration, copy_text) on a black silent card, or None
    idur = intro[0] if intro else 0.0
    lines = []                            # (start, dialogue_string)  -- times already shifted by idur
    hooks = spec.get("hooks", [])
    hook_end = max((min(b, total) for (a, b, txt) in hooks), default=0.0)
    scrim = (r"{\p1\an7\pos(0,0)\1c&H000000&\1a&H9E&\bord0\shad0}"
             "m 0 0 l 1080 0 1080 1920 0 1920{\\p0}")
    # black-card intro copy (no scrim needed; background is already black)
    if intro:
        lines.append((0.0, f"Dialogue: 2,{ts(0)},{ts(idur)},Hook,,0,0,,{acc(intro[1])}"))
    # over-video hooks (+ dim scrim)
    for (a, b, txt) in hooks:
        A, B = a + idur, min(b, total) + idur
        lines.append((A - 0.001, f"Dialogue: 1,{ts(A)},{ts(B)},Scrim,,0,0,,{scrim}"))
        lines.append((A, f"Dialogue: 2,{ts(A)},{ts(B)},Hook,,0,0,,{acc(txt)}"))
    # lyrics (hidden while the opening over-video hook is on screen)
    for (a, b, txt) in caps:
        for (s, e), off in zip(segments, offsets):
            if b <= s or a >= e: continue
            rs = off + (max(a, s) - s); re_ = off + (min(b, e) - s)
            if re_ - rs < 0.15: continue
            if rs < hook_end - 0.2: break
            lines.append((rs + idur, f"Dialogue: 0,{ts(rs+idur)},{ts(re_+idur)},Lyric,,0,0,,{acc(txt)}")); break
    for (a, b, txt) in spec.get("bugs", []):
        A, B = a + idur, min(b, total) + idur
        lines.append((A, f"Dialogue: 2,{ts(A)},{ts(B)},Bug,,0,0,,{acc(txt)}"))
    lines.sort(key=lambda x: x[0])
    with open(ass, "w", encoding="utf-8") as f:
        f.write(HEAD)
        for _, l in lines:
            f.write(l + "\n")

    grade = spec.get("grade", "")
    grade_str = ("," + grade) if grade else ""
    cropx = spec.get("cx", 656)
    fc = []
    seg_labels = []
    if intro:
        fc.append(f"color=c=black:s=1080x1920:r=30:d={idur}[vintro]")
        fc.append(f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=0:{idur}[aintro]")
        seg_labels.append(("vintro", "aintro"))
    for i, (s, e) in enumerate(segments):
        d = e - s
        fc.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,crop=608:1080:{cropx}:0,"
                  f"scale=1080:1920:flags=lanczos{grade_str},fps=30,setsar=1[v{i}]")
        fc.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:st=0:d=0.01,afade=t=out:st={d-0.01:.3f}:d=0.01[a{i}]")
        seg_labels.append((f"v{i}", f"a{i}"))
    cin = "".join(f"[{v}][{a}]" for v, a in seg_labels)
    fc.append(f"{cin}concat=n={len(seg_labels)}:v=1:a=1[cv][ca]")
    fc.append(f"[cv]ass={ass}[vout]")
    out = name + ".mp4"
    cmd = [FFMPEG, "-y", "-ss", f"{seek:.3f}", "-i", SRC, "-filter_complex", ";".join(fc),
           "-map", "[vout]", "-map", "[ca]", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    print(f"=== {out}  ({total+idur:.1f}s) ===", flush=True)
    subprocess.run(cmd, check=True)
    print("done", out, flush=True)


# 別の感情区間：曲のクライマックス（未練）「幸せを探しても…会いたい 心も 身体も」
CAPS = [
    (230.62, 233.44, "«幸せ»を探しても"),
    (233.44, 235.38, "胸に残った"),
    (235.80, 238.38, "過去には勝てないまま"),
    (238.64, 242.00, "«会いたい»、心も"),
    (242.00, 244.00, "身体も"),
    (244.54, 247.50, "あの時と同じでも"),
]

GOLD  = r"{\\c&H4DCCFF&}"   # #FFCC4D honey gold
CREAM = r"{\\c&H7AC5F0&}"   # #F0C57A muted warm (emo)
AMBER = r"{\\c&H2EB0FF&}"   # #FFB02E punchy amber

SEG = (230.62, 247.50)

VIDEOS = [
    {  # A: エモ重視
        "name": "altA_emo", "accent": CREAM, "cx": 656,
        "segments": [SEG], "captions": CAPS,
        "grade": "eq=saturation=0.80:brightness=-0.05:contrast=1.07,vignette=PI/4.2",
        "hooks": [(0.20, 4.60, "«幸せ»を\\N探しても、\\N\\N過去には\\N勝てなかった。")],
        "bugs":  [(13.80, 16.88, "ハニーハニー — SETROUNDLY")],
    },
    {  # B: 楽曲重視
        "name": "altB_song", "accent": GOLD, "cx": 656,
        "segments": [SEG], "captions": CAPS,
        "grade": "eq=saturation=1.05:contrast=1.03:gamma=1.02",
        "hooks": [(0.20, 4.40, "«甘さ»だけを\\N探してた\\N\\N頃の曲。")],
        "bugs":  [(12.20, 16.88, "♪ ハニーハニー / SETROUNDLY\\Nフルはプロフィールから")],
    },
    {  # C: TikTokで伸びる構成
        "name": "altC_viral", "accent": AMBER, "cx": 656,
        "segments": [SEG], "captions": CAPS,
        "grade": "eq=saturation=1.10:contrast=1.05:brightness=0.01",
        "hooks": [(0.10, 4.20, "«会いたい»。\\N\\N心も、\\N身体も。")],
        "bugs":  [(12.20, 16.88, "保存して、夜にもう一回。\\N— SETROUNDLY")],
    },
    {  # 新コピー・案①：黒画面+コピー(ほぼ無音)→歌  ※運営推奨は1.4s
        "name": "new_blackintro", "accent": AMBER, "cx": 656,
        "segments": [SEG], "captions": CAPS,
        "grade": "eq=saturation=1.06:contrast=1.05:brightness=0.005",
        "intro": (1.6, "愛だと\\N思ってた。\\N\\Nたぶん\\N«違った»。"),
        "hooks": [],
        "bugs":  [(12.20, 16.88, "保存して、夜にもう一回。\\N— SETROUNDLY")],
    },
    {  # 新コピー・案②：黒なし、0秒からコピー+歌(暗幕)  ※運営推奨
        "name": "new_overlay", "accent": AMBER, "cx": 656,
        "segments": [SEG], "captions": CAPS,
        "grade": "eq=saturation=1.06:contrast=1.05:brightness=0.005",
        "hooks": [(0.10, 4.20, "愛だと\\N思ってた。\\N\\Nたぶん\\N«違った»。")],
        "bugs":  [(12.20, 16.88, "保存して、夜にもう一回。\\N— SETROUNDLY")],
    },
]

if __name__ == "__main__":
    for s in VIDEOS:
        build(s)
    print("ALL DONE", flush=True)
