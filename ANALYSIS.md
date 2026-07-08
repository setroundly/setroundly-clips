# TikTok 分析（手動データ → results.csv）

ブラウザ自動化は使わず、**Studio で見た数字を入れて分析**する手順です。

## 1. 初回

```bash
python update_results.py --init
```

`results_template.csv` が `tiktok_posts.csv` から作られます。

## 2. 数字を入れる

`update_results.py`（1投稿ずつ）:

```bash
python update_results.py \
  --video-id 7645966686616702224 \
  --views 1200 \
  --two-sec-retention 48 \
  --five-sec-retention 35 \
  --full-watch-rate 14 \
  --avg-watch-time 8.5 \
  --saves 12
```

または Excel で `results.csv` を直接編集（列は `results_schema.py` 参照）。

`tiktok_posts.csv` の `registry_file` に `b01_s1_emo.mp4` などを入れると、編集パラメータ（曲名・フック）と結合されます。

## 3. 分析

```bash
python analyze_results.py
python analyze_results.py --report   # reports/YYYY-MM-DD_analysis.txt にも保存
```

出力: 維持率サマリー、冒頭離脱/完走、伸びた動画の共通点、改善案、次バッチ推奨。

## KPI 優先度

フル視聴率 > 2秒維持 > 5秒維持 > 保存率 > コメント率 > 平均視聴時間
