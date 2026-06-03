# SETROUNDLY_clips

TikTok short clips for SETROUNDLY (live `2026-05-29 SETROUNDLY.mp4`).  
GitHub: `setroundly/setroundly-clips` — **not iam-pro or other projects.**

## Cursor Cloud

- Work in the repo root (`SETROUNDLY_clips`).
- Source concert file: not in Git. On cloud, upload once to the machine or set `SETROUNDLY_SRC` to its path.
- `ffmpeg` is on PATH after `install` in `.cursor/environment.json`.
- Weekly loop: read `weekly_growth_prompt.md`, write reports under `reports/`.
- KPI priority: full watch rate > 2s reach > saves > comments.
- One unique caption per TikTok post.

## Local (Windows)

- Source video default: `../2026-05-29 SETROUNDLY.mp4` (Desktop, next to this folder).
- `python analyze_results.py` after filling `results.csv`.
- `python build_batch.py` / `python build_mc.py` to render (outputs `*.mp4` in repo root, gitignored).
