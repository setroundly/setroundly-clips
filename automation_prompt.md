# SETROUNDLY TikTok インサイト収集（Cloud Agent / 毎日）

リポジトリ: `setroundly/setroundly-clips`（SETROUNDLY_clips ルートで作業）

## 目的

TikTok Studio の **各投稿インサイト** から数値を取り、`results.csv` に記録する。  
特に **2秒・5秒維持率・平均視聴時間・完走率** を週次分析に使う。

## 前提

- **Cloud Desktop** では TikTok ログインが弾かれることが多い → 使わない
- **Cursor の Browser ペイン**（隣のブラウザ）で Studio を開く。ログイン済みならそこから読む
- ログイン・CAPTCHA・2FA が必要なときは **ユーザーに確認を求めて停止**（勝手にパスワード入力しない）

## 毎日の手順

### 1. 準備

```bash
cd SETROUNDLY_clips   # リポジトリルート
python update_results.py --init   # 初回のみ（tiktok_posts.csv から雛形）
```

### 2. TikTok Studio を開く

1. ユーザーに Browser ペインで `https://www.tiktok.com/tiktokstudio` が開けるか確認
2. 未ログインなら「ログインお願いします」と伝え、**ログイン完了まで待つ**
3. **Content → 各投稿 → Analytics / インサイト** を開く（投稿別 Export が無い前提）

### 3. 取得する項目（投稿ごと）

| results.csv 列 | Studio で探すもの |
|----------------|-------------------|
| `date` | 投稿日 |
| `video_id` | 投稿 ID（`tiktok_posts.csv` と一致させる） |
| `title` | キャプション先頭 |
| `views` | 再生 |
| `likes` / `comments` / `shares` / `saves` | 各エンゲージメント |
| `avg_watch_time` | 平均視聴時間（秒） |
| `full_watch_rate` | フル視聴率 / 完走率（%） |
| `two_sec_retention` | 2秒視聴率（%） |
| `five_sec_retention` | 5秒視聴率（%）— 画面に無ければ空欄 |
| `retention_notes` | 補足。取れない項目は **「取得不可」** と書く |

**維持率が画面に無い・読めない場合**

- 該当列は空欄のまま
- `retention_notes` に `2秒維持:取得不可` などと記録
- `views` だけでも `update_results.py` で追記する（エラーにしない）

### 4. results.csv へ追記

Browser から読んだ値を CLI で追記（空欄 OK）:

```bash
python update_results.py \
  --video-id 7645966686616702224 \
  --date "2026-06-03" \
  --title "全部どうでもよかった日に、できた曲。" \
  --views 1200 \
  --likes 40 \
  --comments 3 \
  --saves 12 \
  --avg-watch-time 8.5 \
  --full-watch-rate 14 \
  --two-sec-retention 48 \
  --five-sec-retention 35 \
  --retention-notes ""
```

JSON 一括も可:

```bash
python update_results.py --json imports/studio_batch.json
```

同じ `video_id` は **上書き更新**（重複行を増やさない）。

### 5. tiktok_posts.csv との突合

- `video_id` は `tiktok_posts.csv` と一致させる
- `registry_file` 列（例: `b01_s1_emo.mp4`）を埋めると `analyze_results.py` が編集パラメータと結合できる
- キャプションだけでも突合可能（完全一致 or 部分一致）

### 6. 分析（金曜 or データが揃ったら）

```bash
python analyze_results.py
```

出力: 維持率サマリー、冒頭離脱・完走の良し悪し、伸びた動画の共通点、改善案。

週次レポートが必要なら `weekly_growth_prompt.md` に従い `reports/YYYY-MM-DD_weekly.md` を書く。

## ユーザーへの確認テンプレ

- 「Browser で TikTok Studio にログインできますか？ Desktop ではなく隣のブラウザでお願いします」
- 「投稿 ○○ のインサイト画面を開いたら教えてください」
- 「5秒維持率が画面に無い場合、取得不可で記録してよいですか？」

## やらないこと

- Cloud Desktop でログインを何度も試してアカウントロックを招く
- 投稿別 Export が無いのに Overview だけで全指標が揃ったとみなす
- `results.csv` を手で列ずらしして壊す（必ず `update_results.py` を使う）
