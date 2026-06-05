# TikTok Studio ブラウザ自動化 — 可能性調査（2026-06-03）

## 質問

右側 **Browser ペイン**でログイン済みの TikTok Studio 投稿インサイトを、Cloud Agent が自動操作・DOM 取得できるか。

## 結論（先に）

| 項目 | Cloud Agent（現状） | ローカル Cursor + browse MCP |
|------|----------------------|------------------------------|
| Browser ペインを見る | **×**（VM の外） | **△**（MCP 接続時のみ） |
| 投稿インサイトを開く | VM 上なら △、右ペインは × | **○**（ログイン済みなら可能） |
| 維持率を DOM 取得 | CDP 不可なら × | **○**（要セレクタ調整） |
| `results.csv` 自動追記 | 上記が通れば `update_results.py` に渡すだけ | **○** |

**いまの Cloud Agent セッションから、あなたが開いている右 Browser ペインの中身には直接アクセスできません。**  
VM 内の Chrome（Desktop）とも **別プロセス** です。

---

## 調査で確認したこと

### 1. Cloud Desktop（VNC）の Chrome

- `DISPLAY=:1` のスクリーンショットは取得可能
- 過去セッション: TikTok **ログイン画面でエラー**（`Something went wrong`）
- 今回セッション: Google 新規タブのみ（Studio 未表示）

### 2. 右 Browser ペイン（Cursor 組み込み）

- ユーザーは **ログイン済み・インサイト表示** と報告
- VM の X11 / `ffmpeg x11grab` では **その画面は写らない**
- → **Cursor IDE 側で描画されている別経路**（glass browser / browse daemon）と推定

### 3. Chrome DevTools Protocol（CDP）

- VM 上の Chrome は `--remote-debugging-port=9222` で起動しているが、
- Agent のシェルから `curl http://127.0.0.1:9222/json/list` は **接続失敗**（exit 7）
- → **Playwright の `connect_over_cdp` も Cloud シェルからは現状不可**

### 4. browse MCP / Playwright プラグイン

- Cursor プラグイン `browserbase-browse` に `browser_navigate`, `browser_snapshot`, `browser_evaluate` あり
- Cloud Agent の **このセッションには MCP ツールが未接続**（メタデータのみ届くことがある）
- `browse` CLI はプラグインに `npm install` 前でバイナリ無し

### 5. ヘッドレス Playwright 単体（VM）

- `playwright` + chromium は VM にインストール可能
- 未ログインで Studio URL を開くと **ログイン壁** → インサイト DOM まで到達不可
- Desktop と同様、**ログイン済みセッションの再利用が鍵**

---

## 最小テストコード

```bash
python scripts/probe_tiktok_studio.py
python scripts/probe_tiktok_studio.py --cdp http://127.0.0.1:9222
```

各行が JSON で出力される（`cdp_reachable`, `dom_scrape`, `conclusion` など）。

**期待される Cloud 上の結果:** `cdp_reachable: false` → Playwright CDP スキップ。

**ローカルでログイン済み Chrome + CDP が有効なら:** タブ一覧 → body テキストからメトリクス正規表現マッチ。

---

## DOM 取得について

TikTok Studio は React でクラス名が頻繁に変わる。**本番実装では:**

1. `browser_snapshot`（アクセシビリティツリー）でラベル「2-second video views」等を探す
2. 安定した `data-e2e` / `data-testid` があれば `browser_evaluate` で取得
3. 無い場合は **ラベル隣接テキスト**を正規表現（`probe_tiktok_studio.py` の `METRIC_HINTS`）

維持率が画面に無い投稿は `retention_notes: 取得不可`（`automation_prompt.md` 準拠）。

---

## 取得できる場合の実装案（次フェーズ）

```
automation_prompt.md
    ↓
browser_navigate → tiktokstudio/content
browser_snapshot → 投稿行の ref
browser_click    → 各投稿の Analytics
browser_evaluate → metrics JSON
    ↓
update_results.py --stdin  （1行1 JSON）
    ↓
analyze_results.py
```

擬似コード:

```python
# scripts/fetch_studio_insights.py（未実装・案のみ）
metrics = browser_evaluate(extract_script)
subprocess.run(["python", "update_results.py", "--stdin"], input=json.dumps(metrics))
```

---

## 取得できない場合の代替（優先順）

1. **手動 + `update_results.py`** — いちばん安定（いま運用可能）
2. **`results_template.csv` を Excel 編集** → そのまま分析
3. **チャットに数字貼り付け** → Agent が `update_results.py` 実行
4. **スクショ** — Export が無いときの補助（OCR は最後の手段）
5. **Overview xlsx** — 週次サマリー用のみ（投稿別維持率には不向き）

---

## 次の一手（推奨）

### A. ローカル Cursor で試す（成功率が高い）

1. 右 Browser で Studio インサイトを開いたまま
2. Agent に **browser ツール有効**なセッションで「`probe_tiktok_studio.py` を CDP 接続で実行」と依頼
3. DOM サンプルを1投稿分保存 → セレクタ確定 → `fetch_studio_insights.py` 実装

### B. Cloud Automation のまま

- 右 Browser の中身は Agent から読めないため、**金曜は数字貼り付け or `update_results.py`** を継続
- `resource_exhausted` が解消したら `automation_prompt.md` で手動確認フロー

### C. Browserbase（任意）

- プラグイン `.env` に API キー → ステルスブラウザ + 手動ログイン1回
- 小規模運用ではオーバーキルになりがち

---

## 関連ファイル

- `scripts/probe_tiktok_studio.py` — 最小プローブ
- `update_results.py` — 取得結果の追記先
- `automation_prompt.md` — 日次オペレーション手順
