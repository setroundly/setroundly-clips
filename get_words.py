import json
from faster_whisper import WhisperModel

# windows to get precise word timings for (slightly padded)
WINDOWS = [
    (766.0, 806.0),    # CO2 climax (video1)
    (66.0, 96.0),      # Hanihani chorus (video2)
    (1469.0, 1487.0),  # emo MC (video3)
    (1620.0, 1642.0),  # last-song chorus (video3)
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

with open("words.json", "w", encoding="utf-8") as f:
    json.dump(all_words, f, ensure_ascii=False, indent=1)
print(f"saved words.json ({len(all_words)} words)", flush=True)
print("ALL DONE", flush=True)
