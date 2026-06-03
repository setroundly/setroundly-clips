# SETROUNDLY 週次グロース改善（毎週金曜 21:00 実行）

作業フォルダ: リポジトリ `SETROUNDLY_clips` のルート（ローカル例: `Desktop\SETROUNDLY_clips`）。**GitHub: `setroundly/setroundly-clips`（iam-pro とは別）。**

## 目的
- 金曜夜にデータ集計 → 土日にユーザーが見れるレポートを出す
- 視聴維持率を最優先に、次週の動画編集方針を更新する
- 似た系統のシンガーソングライターTikTokも研究し、編集に反映する

## Step 1: TikTokデータ集計（Phase 2）
1. IDE内ブラウザで TikTok Studio にアクセス（ログインが必要ならユーザーに依頼）
2. Posts / Analytics から公開済み投稿の数値を取得
3. `tiktok_posts.csv`（video_id ↔ ローカルファイル）と突合
4. `results.csv` を更新（列: file, posted_date, views, sec2_rate, avg_watch_s, full_watch_rate, likes, comments, saves, shares, followers_gained）
5. 予約投稿のみで数値0の場合は「公開待ち」と明記し、分析はスキップ可

## Step 2: 自社データ分析
```bash
cd SETROUNDLY_clips   # リポジトリルート
python analyze_results.py
```
- 勝ち: section / style / accent / intro_black / hook
- 負け: 同上。次週は勝ち型を厚く、負け型は削減 or フック差し替え

## Step 3: 競合・トレンドリサーチ（必須）
SETROUNDLYに近い系統（弾き語り・失恋エモ・下北系・一人称ストーリー・広告コピー字幕）のTikTokを調査:
- 検索例: 弾き語り 失恋 / シンガーソングライター ライブ / エモ 邦楽 ショート
- 各3〜5本、以下をメモ:
  - 冒頭1秒のフック（黒画面/コピー/歌詞頭）
  - 字幕: サイズ・改行・色・位置
  - 尺・カット密度・無音の有無
  - キャプションの書き方
- **真似る**: レイアウト・テンポ・コピーの「密度」
- **真似ない**: 自己啓発トーン、感動押し売り、過剰エフェクト

## Step 4: 編集改善の反映
`results.csv` に十分なデータがある場合のみ:
1. `build_batch.py` / `build_mc.py` の VIDEOS 配合を勝ち型寄りに更新
2. 競合リサーチから1〜2点を具体的に反映（例: 改行数、フック秒数、スクリム濃度）
3. 次週分 5〜10本を生成（無理に20本出さない）
4. `python make_registry.py` で registry 更新

## Step 5: 週次レポート（土日用）
`reports/YYYY-MM-DD_weekly.md` に出力:
1. 今週のKPIサマリー（あれば）
2. 勝ち/負けパターン（自社）
3. 競合から学んだ3点
4. 来週の編集方針（具体: 区間・スタイル・フック案3つ）
5. 生成した動画ファイル名一覧

## 運用ルール
- キャプションは**1投稿1コピー**（同文連投しない → A/B紐付け不能）
- 黒イントロはA/Bテスト用。本命は overlay 型を厚く
- 分析に使うKPI優先度: フル視聴率 > 2秒到達 > 保存率 > コメント率
