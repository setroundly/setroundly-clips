# SETROUNDLY 週次グロース改善（毎週金曜 21:00 / Cloud Automation）

作業フォルダ: リポジトリ `SETROUNDLY_clips` のルート。  
GitHub: `setroundly/setroundly-clips`（**iam-pro とは別。このリポジトリ一本**）。

## Cloud Automation 用（Agent Instructions）

SETROUNDLY_clips の週次グロース分析を実行してください。

**まずこのファイル（`weekly_growth_prompt.md`）を全文読み、以下 Step 1〜5 に従ってください。**

優先順位:

1. TikTok Studio の公開済み投稿 KPI を確認（IDE ブラウザ必須）
2. `tiktok_posts.csv` と突合
3. `update_results.py` で `results.csv` を更新
4. `python run_weekly.py --merge` を実行
5. `reports/` に週次レポートを作成
6. `results.csv` に views>0 が 3 本以上あれば `build_batch.py` / `build_mc.py` を更新し、次週用 5〜10 本を生成
7. 最後に変更内容を要約

注意:

- 他プロジェクトには触らない
- **main に存在しないファイルは参照しない**（このファイルと下記スクリプトのみ）
- TikTok Studio へのログインが必要ならユーザーに確認して**停止**（勝手にパスワード入力しない）
- `git commit` はユーザーが明示した場合のみ

### main ブランチで使うファイル

| ファイル | 用途 |
|----------|------|
| `weekly_growth_prompt.md` | この手順書（唯一の週次プロンプト） |
| `tiktok_posts.csv` | 投稿 ID・キャプション ↔ ローカル mp4 |
| `registry.csv` | 編集パラメータ（section / style / hook） |
| `results.csv` | TikTok インサイト（なければ `results_template.csv` から作成） |
| `update_results.py` | Studio 取得データ → `results.csv` |
| `run_weekly.py` | 分析 + `reports/YYYY-MM-DD_weekly.md` |
| `analyze_results.py` | 勝ち負け分析（単体実行可） |
| `scripts/probe_studio_parse.py` | Studio DOM テキストのパーサー（参照用） |
| `build_batch.py` / `build_mc.py` | 次週クリップ生成 |
| `make_registry.py` | registry 更新 |

---

## 目的

- 金曜夜にデータ集計 → 土日にユーザーが見れるレポートを出す
- 視聴維持率を最優先に、次週の動画編集方針を更新する
- 似た系統のシンガーソングライター TikTok も研究し、編集に反映する

## Step 1: TikTok データ集計

1. IDE ブラウザで `https://www.tiktok.com/tiktokstudio` を開く
2. 未ログインならユーザーに依頼して**待つ**
3. **Analytics → Content** で各投稿の **View data** を開く  
   URL 例: `https://www.tiktok.com/tiktokstudio/analytics/{item_id}/overview`
4. 取得項目: views, avg_watch_s, full_watch_rate, likes, comments, saves, shares（維持率は Retention 欄のメモ）
5. `tiktok_posts.csv` の `video_id` / `caption` と突合し `registry.csv` の `file` に紐付け
6. 更新:

```bash
python update_results.py --merge registry
python update_results.py scraped_metrics.json
# または JSON を stdin: python update_results.py --stdin
```

予約のみで views=0 の行はスキップ可（レポートに「公開待ち」）。

## Step 2: 自社データ分析

```bash
python run_weekly.py --merge
```

- 勝ち/負け: section / style / accent / intro_black / hook
- 次週は勝ち型を厚く、負け型は削減 or フック差し替え

## Step 3: 競合・トレンドリサーチ（必須）

SETROUNDLY に近い系統の TikTok を 3〜5 本ずつ調査:

- 検索例: 弾き語り 失恋 / シンガーソングライター ライブ / エモ 邦楽 ショート
- メモ: 冒頭1秒フック、字幕、尺・カット密度、キャプション
- **真似る**: レイアウト・テンポ・コピー密度
- **真似ない**: 自己啓発、感動押し売り、過剰エフェクト

## Step 4: 編集改善の反映

`results.csv` に views>0 が **3 本以上** あるときのみ:

1. `build_batch.py` / `build_mc.py` の VIDEOS を勝ち型寄りに更新
2. 競合から 1〜2 点を ASS に反映
3. 次週 **5〜10 本** 生成（20 本は出さない）
4. `python make_registry.py`

## Step 5: 週次レポート

`reports/YYYY-MM-DD_weekly.md`（`run_weekly.py` が骨子を作成。§3 競合・§4 方針を追記）:

1. 今週の KPI サマリー
2. 勝ち/負けパターン
3. 競合から学んだ 3 点
4. 来週の編集方針（フック案 3 つ）
5. 生成した動画ファイル名一覧

## 運用ルール

- キャプションは **1 投稿 1 コピー**
- KPI 優先: フル視聴率 > 2 秒到達 > 保存 > コメント
- Cloud: Runtime **Cloud**、リポジトリ `setroundly/setroundly-clips` / `main`
- 元動画は Git 外。Cloud では `SETROUNDLY_SRC` またはアップロード
