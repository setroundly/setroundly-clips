# SETROUNDLY_clips

SETROUNDLY 用 TikTok 縦動画の生成・分析専用フォルダ（**iam-pro とは別**）。

## フォルダ構成

| 場所 | 内容 |
|------|------|
| このフォルダ | スクリプト・CSV・レポート・生成 mp4 |
| ひとつ上の Desktop | 元ネタ `2026-05-29 SETROUNDLY.mp4`（Git に入れない） |

## よく使うコマンド

```powershell
cd $env:USERPROFILE\Desktop\SETROUNDLY_clips
python analyze_results.py
python build_batch.py
python make_registry.py
```

## GitHub に上げる（初回だけ）

リポジトリ: **[setroundly/setroundly-clips](https://github.com/setroundly/setroundly-clips)**（`iam-pro` とは別）

初回 push（まだなら）:

```powershell
cd $env:USERPROFILE\Desktop\SETROUNDLY_clips
git add .
git commit -m "SETROUNDLY clips: scripts, registry, weekly workflow"
git branch -M main
git remote add origin https://github.com/setroundly/setroundly-clips.git
git push -u origin main
```

（`remote` は既にある場合は `git remote set-url origin ...`）

[Cloud Agents](https://cursor.com/dashboard?tab=cloud-agents) → **New** → `setroundly/setroundly-clips` を選択  
Automations → Runtime **Cloud** → 同じリポジトリ

## 環境変数（任意）

| 変数 | 意味 |
|------|------|
| `SETROUNDLY_SRC` | 元動画のフルパス |
| `FFMPEG` | ffmpeg 実行ファイル |
