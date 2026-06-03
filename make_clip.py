import sys, json, os, subprocess

# usage: make_clip.py <transcript.json> <start> <end> <out_basename> <ffmpeg_path>
transcript = sys.argv[1]
start = float(sys.argv[2])
end = float(sys.argv[3])
base = sys.argv[4]
ffmpeg = sys.argv[5]
from config import SRC as _src

src = str(_src)
dur = end - start

with open(transcript, encoding="utf-8") as f:
    data = json.load(f)


def ts(sec):
    if sec < 0:
        sec = 0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


srt_path = base + ".srt"
idx = 1
with open(srt_path, "w", encoding="utf-8") as f:
    for seg in data["segments"]:
        s, e = seg["start"], seg["end"]
        if e <= start or s >= end:
            continue
        cs = max(s, start) - start
        ce = min(e, end) - start
        if ce - cs < 0.2:
            continue
        f.write(f"{idx}\n{ts(cs)} --> {ts(ce)}\n{seg['text']}\n\n")
        idx += 1
print(f"wrote {srt_path} with {idx-1} subtitle lines")

style = ("FontName=Yu Gothic UI,FontSize=20,Bold=1,PrimaryColour=&H00FFFFFF,"
         "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,"
         "Alignment=2,MarginV=70")
vf = f"subtitles={os.path.basename(srt_path)}:force_style='{style}'"
out = base + ".mp4"
cmd = [ffmpeg, "-y", "-ss", str(start), "-i", src, "-t", str(dur),
       "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
print("running:", " ".join(cmd))
subprocess.run(cmd, check=True, cwd=os.path.dirname(os.path.abspath(srt_path)))
print("done:", out)
