import subprocess

from config import FFMPEG, SRC

SRC = str(SRC)
FFMPEG = str(FFMPEG)

def ts(t):
    if t < 0: t = 0
    h = int(t//3600); m = int((t%3600)//60); s = t%60
    return f"{h}:{m:02d}:{s:05.2f}"

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Yu Gothic UI,{capsize},&H00FFFFFF,&H000000FF,&H00101010,&H96000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,{capmv},1
Style: Telop,Yu Gothic UI,62,&H0000FAFF,&H000000FF,&H00101010,&H00101010,-1,0,0,0,100,100,0,0,3,16,0,8,70,70,150,1
Style: End,Yu Gothic UI,112,&H00FFFFFF,&H000000FF,&H00101010,&H96000000,-1,0,0,0,100,100,2,0,1,7,4,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""

def build(spec):
    name = spec["name"]
    seek = max(0.0, min(s for s, e in spec["segments"]) - 2.0)
    segments = [(s - seek, e - seek) for s, e in spec["segments"]]
    caps = [(a - seek, b - seek, t) for a, b, t in spec.get("captions", [])]
    offsets = []; acc = 0.0
    for s, e in segments:
        offsets.append(acc); acc += e - s
    total = acc

    ass = name + ".ass"
    lines = []
    for (a, b, txt) in caps:
        for (s, e), off in zip(segments, offsets):
            if b <= s or a >= e: continue
            rs = off + (max(a, s) - s); re_ = off + (min(b, e) - s)
            if re_ - rs < 0.15: continue
            lines.append((rs, f"Dialogue: 0,{ts(rs)},{ts(re_)},Cap,,0,0,,{txt}")); break
    for (a, b, txt) in spec.get("telops", []):
        lines.append((a, f"Dialogue: 1,{ts(a)},{ts(min(b,total))},Telop,,0,0,,{txt}"))
    for (a, b, txt) in spec.get("endcards", []):
        lines.append((a, f"Dialogue: 2,{ts(a)},{ts(min(b,total))},End,,0,0,,{txt}"))
    lines.sort(key=lambda x: x[0])
    with open(ass, "w", encoding="utf-8") as f:
        f.write(HEAD.format(capsize=spec.get("capsize", 80), capmv=spec.get("capmv", 360)))
        for _, l in lines:
            f.write(l + "\n")

    h = spec.get("crop_h", 1080)
    W = round(h * 9 / 16 / 2) * 2
    cx = spec.get("cx", 1040); cy = spec.get("cy", 540)
    x = max(0, min(1920 - W, round(cx - W / 2)))
    y = max(0, min(1080 - h, round(cy - h / 2)))
    grade = spec.get("grade", "")
    grade_str = ("," + grade) if grade else ""

    fc = []
    for i, (s, e) in enumerate(segments):
        d = e - s
        fc.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,crop={W}:{h}:{x}:{y},"
                  f"scale=1080:1920:flags=lanczos{grade_str},fps=30,setsar=1[v{i}]")
        fc.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:st=0:d=0.01,afade=t=out:st={d-0.01:.3f}:d=0.01[a{i}]")
    cin = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    fc.append(f"{cin}concat=n={len(segments)}:v=1:a=1[cv][ca]")
    fc.append(f"[cv]ass={ass}[vout]")
    out = name + ".mp4"
    cmd = [FFMPEG, "-y", "-ss", f"{seek:.3f}", "-i", SRC, "-filter_complex", ";".join(fc),
           "-map", "[vout]", "-map", "[ca]", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    print(f"=== {out}  ({total:.1f}s, crop {W}x{h}@{x},{y}) ===", flush=True)
    subprocess.run(cmd, check=True)
    print("done", out, flush=True)


CAPS = [
    (72.12, 74.12, "ハニーハニー"), (74.12, 78.16, "蜂蜜みたいな"),
    (78.16, 81.04, "まどろみにまみれても"), (81.04, 84.22, "肌に残った針が"),
    (84.22, 86.40, "チクチクしてる"), (86.40, 89.76, "曖昧な匂いも"),
    (89.76, 92.22, "甘さも"), (92.22, 95.24, "あの時と同じでも"),
    (95.24, 98.00, "この夜は"), (98.00, 101.50, "いっそ いっそ ぬかるでさ"),
]

VIDEOS = [
    {  # 動画1: 盛り上がり / スクロール停止 (wide, punchy grade)
        "name": "chorus1_peak", "segments": [(72.10, 77.00), (78.10, 101.60)],
        "captions": CAPS, "crop_h": 1080, "cx": 1040, "cy": 540,
        "grade": "eq=saturation=1.12:contrast=1.05:brightness=0.01",
        "telops": [(0.20, 3.60, "無名だけど、曲は本気です"),
                   (3.80, 7.40, "ライブハウスで見つけたバンド")],
        "endcards": [(25.70, 28.40, "SETROUNDLY")],
    },
    {  # 動画2: 曲推し (full-height, clean, big lyrics)
        "name": "chorus2_song", "segments": [(72.10, 101.60)],
        "captions": CAPS, "crop_h": 1080, "cx": 1040, "cy": 540, "capsize": 94, "capmv": 330,
        "grade": "eq=saturation=1.04:contrast=1.02",
        "telops": [(0.20, 3.20, "このサビ、どう思う？"),
                   (23.50, 29.50, "もっと聴きたいなら保存\\N@SETROUNDLY")],
    },
    {  # 動画3: エモ (full-height, cool dark grade, vignette)
        "name": "chorus3_emo", "segments": [(72.10, 101.60)],
        "captions": CAPS, "crop_h": 1080, "cx": 1040, "cy": 540,
        "grade": "eq=saturation=0.80:brightness=-0.05:contrast=1.07,vignette=PI/4.2",
        "telops": [(0.20, 4.50, "夜に、ひとりで聴いてほしい")],
        "endcards": [(26.80, 29.50, "続きはライブハウスで\\NSETROUNDLY")],
    },
]

if __name__ == "__main__":
    for s in VIDEOS:
        build(s)
    print("ALL DONE", flush=True)
