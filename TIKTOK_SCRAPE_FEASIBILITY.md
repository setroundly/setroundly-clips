# TikTok Studio 自動取得 — 可能性調査（2026-06-03）

## 結論サマリー

| # | 項目 | 判定 |
|---|------|------|
| 1 | Cursor Browser ペインで Studio 自動操作 | **可**（クリック・遷移・CDP 確認済み） |
| 2 | 投稿インサイトページを開く | **可**（Analytics > Content > `View data`） |
| 3 | 維持率・平均視聴・完走率を DOM 取得 | **可**（`document.body.innerText` で安定） |
| 4 | `results.csv` 自動追記 | **可**（`update_results.py` と組み合わせ） |
| 5 | 単体 Playwright（別プロセス） | **条件付き**（Cookie / ログインセッション要移植） |

**推奨方針**: 金曜 Automation は **Cursor Cloud Agent + IDE ブラウザ（MCP）** で操作し、DOM テキストを `scripts/probe_studio_parse.py` でパース → `update_results.py`。**別途 Playwright 常駐は不要**（Glass ブラウザが実質 Playwright/CDP 層）。

---

## 1. 自動操作（実測）

- Posts 一覧: `https://www.tiktok.com/tiktokstudio/content`
- Analytics Content: `https://www.tiktok.com/tiktokstudio/analytics/content`
- 投稿インサイト URL パターン:

```
https://www.tiktok.com/tiktokstudio/analytics/{analytics_item_id}/overview
https://www.tiktok.com/tiktokstudio/analytics/{analytics_item_id}/engagement
```

`View data` クリックで遷移（例: `7645966746758712592`）。

**注意**: `analytics_item_id` ≠ 公開 URL の `video_id`（`@user/video/7645966727318179089`）。突合は **キャプション + 投稿日 + views** で `tiktok_posts.csv` / `registry.csv` に紐付ける。

---

## 2. DOM から取れた指標（1本テスト）

| 指標 | 取得 | 例 |
|------|------|-----|
| views | ○ | 389 |
| likes / comments / shares / saves | ○ | 8 / 0 / 1 / 3 |
| avg_watch_s | ○ | 11.32 |
| full_watch_rate | ○ | 13.2% |
| retention_note | ○ | "stopped at 0:01" |
| sec2_rate（2秒視聴率） | △ | Overview にラベルなし。Retention グラフの `0:02 (xx%)` から推定するか、Download data CSV を要確認 |

---

## 3. 実装案（次フェーズ）

```
weekly Automation
  ├─ browser: analytics/content を開く
  ├─ 各行の [View data] を順にクリック（または item_id URL を直叩き）
  ├─ CDP Runtime.evaluate → innerText
  ├─ probe_studio_parse.parse_overview_text()
  ├─ caption で registry file にマップ
  └─ update_results.py --stdin → run_weekly.py
```

Posts 一覧だけなら views/likes/comments は **一覧 DOM のみ** で足りる（インサイト不要）。**完走率・平均視聴はインサイト必須**。

---

## 4. Playwright 単体の場合

```python
# scripts/probe_playwright_connect.py（将来用・未接続）
# playwright install chromium
# context = chromium.launch_persistent_context(user_data_dir)  # Studio ログイン済みプロファイル
```

- Cloud Agent の Glass ブラウザと **Cookie を共有しない** ため、Playwright 単体は再ログイン or Cookie エクスポートが必要。
- ローカル常駐バッチなら `user_data_dir` 方式は有効。

---

## 5. 取得できない場合の代替（現時点では不要）

優先度低（DOM 取得が成功したため）:

1. **Download data** ボタン（Analytics 画面）→ CSV 手動/半自動
2. **スクリーンショット + Vision**（DOM 変更時のフォールバック）
3. **手動 JSON** → `update_results.py --stdin`

---

## 6. 最小テスト

```powershell
python scripts/probe_studio_parse.py
```

実ブラウザ連携テストは Automation 初回 Run またはチャットで「Posts から1本インサイト取得テスト」。
