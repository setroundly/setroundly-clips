import os, subprocess
from faster_whisper import WhisperModel

from config import FFMPEG, SRC

SRC = str(SRC)
FFMPEG = str(FFMPEG)

# name, start, end
WINDOWS = [
    ("tt_hook1_opening", 3.0, 18.3),
    ("tt_hook2_music",   1472.5, 1484.7),
    ("tt_hook3_lyric",   1623.5, 1638.6),
]

MAX_CHARS = 13         # max japanese chars per caption
MAX_DUR = 2.6          # max seconds per caption
GAP_SPLIT = 0.5        # split if pause longer than this

print("loading medium model ...", flush=True)
model = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=8)


def ass_ts(t):
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,Yu Gothic UI,84,&H00FFFFFF,&H0000F0FF,&H00202020,&H96000000,-1,0,0,0,100,100,1,0,1,6,3,2,40,40,330,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""


def build_events(words):
    events = []
    cur, c_start, c_end, prev_end = "", None, None, None
    PUNC = "、。！？!?"
    for w in words:
        txt = w.word.strip().replace(" ", "")
        if not txt:
            continue
        clean = txt.strip(PUNC)
        if c_start is None:
            c_start = w.start
        gap = (w.start - prev_end) if prev_end is not None else 0
        # flush before adding if needed
        if cur and (len(cur) >= MAX_CHARS or (c_end - c_start) >= MAX_DUR or gap > GAP_SPLIT):
            events.append((c_start, c_end, cur))
            cur, c_start = "", w.start
        cur += clean
        c_end = w.end
        prev_end = w.end
        # flush on sentence punctuation
        if any(p in txt for p in PUNC) and cur:
            events.append((c_start, c_end, cur))
            cur, c_start, c_end = "", None, None
    if cur:
        events.append((c_start, c_end, cur))
    # merge tiny orphan chunks (<3 chars) into the neighbour
    merged = []
    for s, e, t in events:
        if merged and len(t) < 3 and (s - merged[-1][1]) < GAP_SPLIT:
            ps, pe, pt = merged[-1]
            merged[-1] = (ps, e, pt + t)
        else:
            merged.append((s, e, t))
    events = merged
    # extend last event end slightly, avoid overlaps
    fixed = []
    for i, (s, e, t) in enumerate(events):
        if i + 1 < len(events):
            e = min(e + 0.15, events[i + 1][0] - 0.01)
        fixed.append((s, max(e, s + 0.3), t))
    return fixed


for name, start, end in WINDOWS:
    segments, info = model.transcribe(
        "audio.wav", language="ja", beam_size=5,
        clip_timestamps=f"{start},{end}", word_timestamps=True,
        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=250),
    )
    words = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                if start <= w.start <= end:
                    words.append(w)
    events = build_events(words)
    ass_path = name + ".ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, t in events:
            rs, re_ = max(s - start, 0), max(e - start, 0)
            f.write(f"Dialogue: 0,{ass_ts(rs)},{ass_ts(re_)},Pop,,0,0,,{t}\n")
            print(f"{name}  {rs:5.2f}-{re_:5.2f}  {t}", flush=True)

    dur = end - start
    vf = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:2,eq=brightness=-0.06[bgb];"
        "[fg]scale=1080:-2[fgs];"
        "[bgb][fgs]overlay=(W-w)/2:(H-h)/2[base];"
        f"[base]ass={ass_path}[v]"
    )
    out = name + ".mp4"
    cmd = [FFMPEG, "-y", "-ss", str(start), "-i", SRC, "-t", str(dur),
           "-filter_complex", vf, "-map", "[v]", "-map", "0:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    print("rendering", out, flush=True)
    subprocess.run(cmd, check=True)
    print("done", out, "\n", flush=True)

print("ALL DONE", flush=True)
