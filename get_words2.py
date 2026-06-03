import json
from faster_whisper import WhisperModel

WINDOWS = [
    (88.0, 102.5),     # Hanihani chorus tail (video2)
    (1453.0, 1462.5),  # emo MC nostalgia (video3)
    (808.0, 815.0),    # CO2 outro MC "CO2という曲" (video1)
]

print("loading medium model ...", flush=True)
model = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=8)

all_words = []
for start, end in WINDOWS:
    segments, info = model.transcribe(
        "audio.wav", language="ja", beam_size=5,
        clip_timestamps=f"{start},{end}", word_timestamps=True,
        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=200),
    )
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            if start - 0.1 <= w.start <= end + 0.1:
                all_words.append({"start": round(w.start, 2), "end": round(w.end, 2),
                                   "text": w.word.strip()})
                print(f"  {w.start:8.2f}-{w.end:8.2f}  {w.word.strip()}", flush=True)
    print(f"--- window {start}-{end} done ---", flush=True)

with open("words2.json", "w", encoding="utf-8") as f:
    json.dump(all_words, f, ensure_ascii=False, indent=1)
print("ALL DONE", flush=True)
