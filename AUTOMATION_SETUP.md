# Cloud Automation セットアップ

週次手順の本体は **`weekly_growth_prompt.md`** のみです（このファイルに統合済み）。

## 設定

| 項目 | 値 |
|------|-----|
| リポジトリ | `setroundly/setroundly-clips` |
| ブランチ | `main` |
| Runtime | **Cloud** |
| トリガー | 毎週金曜 21:00 GMT+9 |
| 指示 | `weekly_growth_prompt.md` を全文読んで実行 |

下書き: `.cursor/weekly-automation-prefill.json`

## 初回のみ

1. Cloud に元動画（`SETROUNDLY_SRC` またはアップロード）
2. Automation 初回で TikTok Studio ログイン（Browser ペイン）

## Run Test が `resource_exhausted` のとき

Cursor Cloud の実行枠不足。時間をおいて再試行するか、[Cloud Agents ダッシュボード](https://cursor.com/dashboard?tab=cloud-agents) で上限を確認。
