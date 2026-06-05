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

## Local (Windows)

- Source: `../2026-05-29 SETROUNDLY.mp4`
- `python run_weekly.py --merge` after `update_results.py`
- `python build_batch.py` / `python build_mc.py` → `*.mp4` (gitignored)
