# SETROUNDLY_clips

SETROUNDLY 用 TikTok 縦動画の生成・分析専用フォルダ（**iam-pro とは別**）。

## フォルダ構成

| 場所 | 内容 |
|------|------|
| このフォルダ | スクリプト・CSV・レポート・生成 mp4 |
| ひとつ上の Desktop | 元ネタ `2026-05-29 SETROUNDLY.mp4`（Git に入れない） |

## 週次フル自動化（金曜 21:00）

**手順の本体**: [`weekly_growth_prompt.md`](weekly_growth_prompt.md)  
Cloud 設定メモ: [`AUTOMATION_SETUP.md`](AUTOMATION_SETUP.md)

## よく使うコマンド

```powershell
cd $env:USERPROFILE\Desktop\SETROUNDLY_clips
python run_weekly.py --merge
python update_results.py --merge registry
python analyze_results.py
python build_batch.py
python make_registry.py
```

## GitHub

リポジトリ: **[setroundly/setroundly-clips](https://github.com/setroundly/setroundly-clips)**

[Cloud Agents](https://cursor.com/dashboard?tab=cloud-agents) → `setroundly/setroundly-clips` / **main**  
Automations → Runtime **Cloud** → 指示は `weekly_growth_prompt.md`

## 環境変数（任意）

| 変数 | 意味 |
|------|------|
| `SETROUNDLY_SRC` | 元動画のフルパス |
| `FFMPEG` | ffmpeg 実行ファイル |
