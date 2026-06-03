import subprocess, os

from config import FFMPEG, SRC

SRC = str(SRC)
FFMPEG = str(FFMPEG)
CX = 656  # center crop x for 608-wide 9:16 crop

def ts(t):
    if t < 0: t = 0
    h = int(t//3600); m = int((t%3600)//60); s = t%60
    return f"{h}:{m:02d}:{s:05.2f}"

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Yu Gothic UI,80,&H00FFFFFF,&H000000FF,&H00101010,&H96000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,360,1
Style: Telop,Yu Gothic UI,62,&H0000FAFF,&H000000FF,&H00101010,&H00101010,-1,0,0,0,100,100,0,0,3,16,0,8,70,70,150,1
Style: End,Yu Gothic UI,116,&H00FFFFFF,&H000000FF,&H00101010,&H96000000,-1,0,0,0,100,100,2,0,1,7,4,5,80,80,0,1
Style: Sub,Yu Gothic UI,52,&H00FFFFFF,&H000000FF,&H00101010,&H96000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""

def map_time(t, segments, offsets):
    for (s, e), off in zip(segments, offsets):
        if s - 0.05 <= t <= e + 0.05:
            return off + (min(max(t, s), e) - s)
    return None

def build(spec):
    name = spec["name"]
    seek = max(0.0, min(s for s, e in spec["segments"]) - 2.0)
    segments = [(s - seek, e - seek) for s, e in spec["segments"]]
    spec_captions = [(a - seek, b - seek, t) for a, b, t in spec.get("captions", [])]
    durs = [e - s for s, e in segments]
    offsets = []
    acc = 0.0
    for d in durs:
        offsets.append(acc); acc += d
    total = acc

    ass = name + ".ass"
    lines = []
    # captions (source-time based) -> timeline
    for (a, b, txt) in spec_captions:
        for (s, e), off in zip(segments, offsets):
            if b <= s or a >= e:
                continue
            rs = off + (max(a, s) - s)
            re_ = off + (min(b, e) - s)
            if re_ - rs < 0.15:
                continue
            lines.append((rs, f"Dialogue: 0,{ts(rs)},{ts(re_)},Cap,,0,0,,{txt}"))
            break
    # telops (timeline-time based)
    for (a, b, txt) in spec.get("telops", []):
        lines.append((a, f"Dialogue: 1,{ts(a)},{ts(min(b,total))},Telop,,0,0,,{txt}"))
    # endcard (timeline)
    for (a, b, txt) in spec.get("endcards", []):
        lines.append((a, f"Dialogue: 2,{ts(a)},{ts(min(b,total))},End,,0,0,,{txt}"))
    lines.sort(key=lambda x: x[0])

    with open(ass, "w", encoding="utf-8") as f:
        f.write(ASS_HEAD)
        for _, l in lines:
            f.write(l + "\n")

    # filter_complex
    fc = []
    for i, (s, e) in enumerate(segments):
        d = e - s
        fc.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,crop=608:1080:{CX}:0,"
                  f"scale=1080:1920:flags=lanczos,fps=30,setsar=1[v{i}]")
        fc.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:st=0:d=0.01,afade=t=out:st={d-0.01:.3f}:d=0.01[a{i}]")
    concat_in = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    fc.append(f"{concat_in}concat=n={len(segments)}:v=1:a=1[cv][ca]")
    fc.append(f"[cv]ass={ass}[vout]")
    filter_complex = ";".join(fc)

    out = name + ".mp4"
    cmd = [FFMPEG, "-y", "-ss", f"{seek:.3f}", "-i", SRC, "-filter_complex", filter_complex,
           "-map", "[vout]", "-map", "[ca]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    print(f"=== rendering {out}  (total {total:.1f}s, {len(segments)} cuts) ===", flush=True)
    subprocess.run(cmd, check=True)
    print("done", out, "\n", flush=True)


VIDEOS = [
    {  # 動画1: 一番盛り上がる瞬間 (CO2 climax) ~30s
        "name": "short1_peak",
        "segments": [(776.40, 787.40), (788.70, 803.50), (809.36, 814.30)],
        "captions": [
            (776.42, 779.00, "歌うよ 歌うよ 歌うよ"),
            (781.30, 787.30, "このまま…"),
            (788.76, 792.88, "このまま…"),
            (792.88, 794.72, "貰ったこと"),
            (794.72, 799.00, "忘れないように"),
            (799.88, 801.24, "ありがとう！"),
            (811.70, 813.02, "「CO2」という曲です"),
        ],
        "telops": [
            (0.20, 3.60, "無名だけど、曲は本気です"),
            (3.80, 7.40, "ライブハウスで見つけたバンド"),
            (8.00, 11.80, "全部ひとり、弾き語りです"),
        ],
        "endcards": [(28.20, 30.70, "SETROUNDLY")],
    },
    {  # 動画2: 曲推し (Hanihani chorus) ~29.5s
        "name": "short2_song",
        "segments": [(72.10, 101.60)],
        "captions": [
            (72.12, 74.12, "ハニーハニー"),
            (74.12, 78.16, "蜂蜜みたいな"),
            (78.16, 81.04, "まどろみにまみれても"),
            (81.04, 84.22, "肌に残った針が"),
            (84.22, 86.40, "チクチクしてる"),
            (86.40, 89.76, "曖昧な匂いも"),
            (89.76, 92.22, "甘さも"),
            (92.22, 95.24, "あの時と同じでも"),
            (95.24, 98.00, "この夜は"),
            (98.00, 101.50, "いっそ いっそ ぬかるでさ"),
        ],
        "telops": [
            (0.20, 3.20, "このサビ、どう思う？"),
            (23.50, 29.50, "もっと聴きたいなら保存\\N@SETROUNDLY"),
        ],
    },
    {  # 動画3: エモ・ストーリー (emo MC -> last-song chorus) ~29.5s
        "name": "short3_emo",
        "segments": [(1454.18, 1461.66), (1473.60, 1479.50), (1623.26, 1639.40)],
        "captions": [
            (1454.18, 1456.90, "今日みたいに晴れた日に"),
            (1457.90, 1461.66, "懐かしい曲を流しながら走ってた"),
            (1473.60, 1474.30, "音楽…"),
            (1474.74, 1477.00, "大人になると聞けなくなる"),
            (1477.00, 1479.48, "わかんないですか？大好きですか？"),
            (1623.26, 1626.20, "悲しくないことを悲しまないで"),
            (1626.26, 1629.08, "それはいつかの君が"),
            (1629.08, 1632.46, "眠れない夜にこぼした"),
            (1632.46, 1634.18, "涙でできた"),
            (1634.18, 1639.40, "透明な傘があるから"),
        ],
        "telops": [
            (0.20, 4.80, "仕事しながら、バンド続けてます"),
            (8.00, 12.80, "大人になると、音楽は…"),
        ],
        "endcards": [(26.80, 29.50, "続きはライブハウスで\\NSETROUNDLY")],
    },
]

if __name__ == "__main__":
    for spec in VIDEOS:
        build(spec)
    print("ALL DONE", flush=True)
