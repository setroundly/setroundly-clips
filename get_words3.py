import json
from faster_whisper import WhisperModel

WINDOWS = [
    (122.0, 141.0),   # "見せかけの優しさなんて本当にいらない"
    (218.0, 248.0),   # "幸せを探しても...会いたい心も あの時と同じでも"
    (192.0, 215.0),   # "肌に残った針がチクチク / 曖昧匂いも あの時と同じで"
]

print("loading medium model ...", flush=True)
model = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=8)

allw = []
for start, end in WINDOWS:
    segs, info = model.transcribe(
        "audio.wav", language="ja", beam_size=5,
        clip_timestamps=f"{start},{end}", word_timestamps=True,
        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=200),
    )
    print(f"\n##### window {start}-{end} #####", flush=True)
    for seg in segs:
        if not seg.words:
            continue
        for w in seg.words:
            if start - 0.1 <= w.start <= end + 0.1:
                allw.append({"start": round(w.start, 2), "end": round(w.end, 2), "text": w.word.strip()})
                print(f"  {w.start:8.2f}-{w.end:8.2f}  {w.word.strip()}", flush=True)

with open("words3.json", "w", encoding="utf-8") as f:
    json.dump(allw, f, ensure_ascii=False, indent=1)
print("ALL DONE", flush=True)
