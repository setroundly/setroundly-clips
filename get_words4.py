import json
from faster_whisper import WhisperModel

WINDOWS = [
    (883.0, 919.0),    # A: アコギ修行の苦い思い出
    (284.0, 328.0),    # B: ブルー/アラフォー 自虐
    (1389.0, 1449.0),  # C: 原付ノスタルジー
]

print("loading medium model ...", flush=True)
model = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=8)

allw = []
for start, end in WINDOWS:
    segs, info = model.transcribe(
        "audio.wav", language="ja", beam_size=5,
        clip_timestamps=f"{start},{end}", word_timestamps=True,
        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=300),
    )
    print(f"\n##### window {start}-{end} #####", flush=True)
    for seg in segs:
        if not seg.words:
            continue
        # print segment-level line too for easy reading
        print(f"  [SEG {seg.start:7.2f}-{seg.end:7.2f}] {seg.text.strip()}", flush=True)
        for w in seg.words:
            if start - 0.1 <= w.start <= end + 0.1:
                allw.append({"start": round(w.start, 2), "end": round(w.end, 2), "text": w.word.strip()})

with open("words4.json", "w", encoding="utf-8") as f:
    json.dump(allw, f, ensure_ascii=False, indent=1)
print("ALL DONE", flush=True)
