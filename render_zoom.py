import subprocess

from config import FFMPEG, SRC

SRC = str(SRC)
FFMPEG = str(FFMPEG)

# name, start, end, crop_x (left offset for the 608-wide center crop; 656 = exact center)
CLIPS = [
    ("tt_hook1_opening", 3.0, 18.3, 656),
    ("tt_hook2_music",   1472.5, 1484.7, 656),
    ("tt_hook3_lyric",   1623.5, 1638.6, 656),
]

for name, start, end, cx in CLIPS:
    dur = end - start
    vf = f"crop=608:1080:{cx}:0,scale=1080:1920:flags=lanczos,ass={name}.ass"
    out = name + ".mp4"
    cmd = [FFMPEG, "-y", "-ss", str(start), "-i", SRC, "-t", str(dur),
           "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    print("rendering", out, flush=True)
    subprocess.run(cmd, check=True)
    print("done", out, flush=True)

print("ALL DONE", flush=True)
