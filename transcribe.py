import sys, json, datetime
from faster_whisper import WhisperModel

audio = sys.argv[1]
out_json = sys.argv[2]
model_size = sys.argv[3] if len(sys.argv) > 3 else "small"
start = float(sys.argv[4]) if len(sys.argv) > 4 else None
end = float(sys.argv[5]) if len(sys.argv) > 5 else None

print(f"loading model {model_size} ...", flush=True)
model = WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=8)

kwargs = dict(language="ja", beam_size=5, vad_filter=True,
              vad_parameters=dict(min_silence_duration_ms=400))
if start is not None:
    kwargs["clip_timestamps"] = f"{start},{end}"

segments, info = model.transcribe(audio, **kwargs)

data = []
for s in segments:
    data.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    print(f"[{s.start:7.2f} -> {s.end:7.2f}] {s.text.strip()}", flush=True)

with open(out_json, "w", encoding="utf-8") as f:
    json.dump({"duration": info.duration, "segments": data}, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(data)} segments to {out_json}", flush=True)
