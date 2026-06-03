import wave, numpy as np

wf = wave.open("audio.wav", "rb")
sr = wf.getframerate()
n = wf.getnframes()
raw = wf.readframes(n)
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
print(f"sr={sr} dur={n/sr:.1f}s", flush=True)

win = int(sr * 0.5)  # 0.5s bins
hop = win
rms = []
times = []
for i in range(0, len(x) - win, hop):
    seg = x[i:i + win]
    r = np.sqrt(np.mean(seg ** 2)) + 1e-9
    db = 20 * np.log10(r)
    rms.append(db)
    times.append(i / sr)
rms = np.array(rms)
times = np.array(times)

# loudest 1s windows (sustained energy) across whole track
order = np.argsort(rms)[::-1]
print("\n=== Loudest 0.5s bins (top 30) ===", flush=True)
seen = []
for idx in order:
    t = times[idx]
    if any(abs(t - s) < 4 for s in seen):
        continue
    seen.append(t)
    print(f"  t={t:7.1f}s  {rms[idx]:6.1f} dB", flush=True)
    if len(seen) >= 30:
        break

# energy around known song-end / applause moments
print("\n=== Energy around song boundaries (applause check) ===", flush=True)
for label, c in [("song1 end ~101", 101), ("MC end ~277", 277), ("cheek end ~524", 524),
                  ("CO2 end ~800", 800), ("answer end ~1320", 1320),
                  ("last1 ~1791", 1791), ("end ~1801", 1801)]:
    mask = (times >= c - 6) & (times <= c + 8)
    if mask.any():
        seg = rms[mask]
        print(f"  {label}: mean {seg.mean():.1f} max {seg.max():.1f} dB", flush=True)

# silence regions (below -45 dB for >0.8s)
print("\n=== Quiet/near-silent bins (< -42 dB) ===", flush=True)
quiet = times[rms < -42]
if len(quiet):
    # group consecutive
    groups = []
    start = prev = quiet[0]
    for t in quiet[1:]:
        if t - prev > 1.0:
            groups.append((start, prev))
            start = t
        prev = t
    groups.append((start, prev))
    for s, e in groups:
        if e - s >= 0.5:
            print(f"  {s:7.1f} - {e:7.1f}s ({e-s:.1f}s)", flush=True)
