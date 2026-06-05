# SETROUNDLY_clips

TikTok short clips for SETROUNDLY (live `2026-05-29 SETROUNDLY.mp4`).  
GitHub: `setroundly/setroundly-clips` — **not iam-pro. 運用はこのリポジトリ一本。**

## Weekly automation (primary)

- **唯一の手順書**: `weekly_growth_prompt.md`（Cloud Automation もこれを読む）
- Pipeline: TikTok Studio (browser) → `update_results.py` → `run_weekly.py` → competitor research → `build_batch.py` / `build_mc.py` → `reports/`
- Prefill: `.cursor/weekly-automation-prefill.json`

## Cursor Cloud

- Repo root only. Branch: `main`.
- Source video: not in Git; set `SETROUNDLY_SRC` or upload on Cloud.
- `ffmpeg` on PATH after `install` in `.cursor/environment.json`.
- KPI: full watch rate > 2s reach > saves > comments.

## Cursor Cloud specific instructions

This repo is an **offline CLI toolkit** (Python + ffmpeg). There is no dev server, Docker stack, or configured lint/test suite.

### Dependencies

- System: `ffmpeg` (apt in `.cursor/environment.json` `install`).
- Python: `pip3 install -r requirements.txt` (add `numpy` if you run `analyze_audio.py`).

### Source video (required for `build_*.py`)

Default path `../2026-05-29 SETROUNDLY.mp4` does not exist on cloud VMs. Either upload the concert file and `export SETROUNDLY_SRC=/path/to/2026-05-29 SETROUNDLY.mp4`, or generate a long-enough stand-in (batch segments need timestamps up to ~1640s):

```bash
ffmpeg -y -f lavfi -i testsrc2=size=1920x1080:rate=30 -f lavfi -i sine=frequency=440:sample_rate=48000 \
  -t 1800 -c:v libx264 -preset ultrafast -crf 28 -c:a aac /tmp/setroundly-test-src.mp4
export SETROUNDLY_SRC=/tmp/setroundly-test-src.mp4
```

### Common commands (from repo root)

| Task | Command |
|------|---------|
| Init TikTok metrics template | `python3 analyze_results.py --init` → fill `results_template.csv` → save as `results.csv` |
| Analyze posted clips | `python3 analyze_results.py` |
| Render A/B batch (~20 clips) | `python3 build_batch.py` |
| Render MC clips | `python3 build_mc.py` |
| Regenerate `registry.csv` | `python3 make_registry.py` |
| Single pattern variant set | `python3 build_patterns.py` |

Outputs are `*.mp4` in the repo root (gitignored). `config.py` resolves `SRC`, `FFMPEG`, and `REPORTS`.

### Smoke test without the real concert

```bash
export SETROUNDLY_SRC=/path/to/test-src.mp4   # ≥300s is enough for one `build_patterns` clip
python3 -c "from build_patterns import build, VIDEOS; build(VIDEOS[0])"
```

`faster-whisper` downloads models on first transcription run (`transcribe.py`, `get_words*.py`); not needed for re-renders that use existing ASS timings.

## Local (Windows)

- Source: `../2026-05-29 SETROUNDLY.mp4`
- `python run_weekly.py --merge` after `update_results.py`
- `python build_batch.py` / `python build_mc.py` → `*.mp4` (gitignored)
