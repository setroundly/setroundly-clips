import json
from faster_whisper import WhisperModel

windows = [
    ("clip1", 3.0, 18.3),
    ("clip2", 1472.5, 1487.5),
    ("clip3", 1623.5, 1638.6),
]

print("loading medium model ...", flush=True)
model = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=8)

for name, start, end in windows:
    segments, info = model.transcribe(
        "audio.wav", language="ja", beam_size=5,
        clip_timestamps=f"{start},{end}",
        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=300),
    )
    data = []
    for s in segments:
        st = max(s.start, start)
        en = min(s.end, end)
        data.append({"start": round(st, 2), "end": round(en, 2), "text": s.text.strip()})
        print(f"{name} [{st:7.2f} -> {en:7.2f}] {s.text.strip()}", flush=True)
    with open(name + ".json", "w", encoding="utf-8") as f:
        json.dump({"segments": data}, f, ensure_ascii=False, indent=2)
    print(f"saved {name}.json ({len(data)} segs)\n", flush=True)

print("ALL DONE", flush=True)
