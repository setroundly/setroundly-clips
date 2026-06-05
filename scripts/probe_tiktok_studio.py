#!/usr/bin/env python3
"""最小テスト: Browser / Playwright から TikTok Studio インサイトを読めるか調査する。

使い方:
  python scripts/probe_tiktok_studio.py
  python scripts/probe_tiktok_studio.py --cdp http://127.0.0.1:9222
  python scripts/probe_tiktok_studio.py --url https://www.tiktok.com/tiktokstudio/content

前提:
  - ログイン済み Chrome に CDP で繋がれる環境でのみ DOM 取得が成功する
  - Cloud VM の Agent シェルからは CDP 9222 に届かないことが多い（調査結果参照）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone

CDP_DEFAULT = "http://127.0.0.1:9222"

# Studio 画面から雑に拾うキーワード（本番は data-testid 等に差し替え）
METRIC_HINTS = [
    ("views", r"(?:Views|再生|ビュー|Video views)[^\d]*([\d,]+)"),
    ("likes", r"(?:Likes|いいね)[^\d]*([\d,]+)"),
    ("comments", r"(?:Comments|コメント)[^\d]*([\d,]+)"),
    ("shares", r"(?:Shares|シェア)[^\d]*([\d,]+)"),
    ("saves", r"(?:Saves|保存)[^\d]*([\d,]+)"),
    ("avg_watch_time", r"(?:Avg\.? watch time|平均視聴時間)[^\d]*([\d.,]+)"),
    ("full_watch_rate", r"(?:Full video watch rate|フル視聴|完走)[^\d]*([\d.,]+)\s*%?"),
    ("two_sec_retention", r"(?:2[-\s]?second|2秒)[^\d]*([\d.,]+)\s*%?"),
    ("five_sec_retention", r"(?:5[-\s]?second|5秒)[^\d]*([\d.,]+)\s*%?"),
]


def report(step: str, ok: bool, detail: str, **extra):
    payload = {
        "step": step,
        "ok": ok,
        "detail": detail,
        "ts": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return ok


def probe_cdp_reachable(cdp_url: str) -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(f"{cdp_url.rstrip('/')}/json/version", timeout=3) as r:
            data = json.loads(r.read().decode())
        return report("cdp_reachable", True, data.get("Browser", "unknown"), version=data)
    except Exception as e:
        return report("cdp_reachable", False, str(e))


def probe_playwright_cdp(cdp_url: str, target_url: str | None) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return report("playwright_import", False, "pip install playwright && python -m playwright install chromium")

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            contexts = browser.contexts
            if not contexts:
                return report("playwright_contexts", False, "no browser contexts on CDP")

            pages = [pg for ctx in contexts for pg in ctx.pages]
            report("playwright_pages", True, f"{len(pages)} open tab(s)", titles=[pg.title() for pg in pages])

            page = None
            for pg in pages:
                if "tiktok" in (pg.url or "").lower():
                    page = pg
                    break
            if page is None and pages:
                page = pages[0]
            if page is None and target_url:
                page = contexts[0].new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            if page is None:
                return report("playwright_page", False, "no page to inspect")

            report("playwright_active", True, page.url, title=page.title())

            # インサイトらしきテキストを body から抽出（セレクタ未確定のため最小テスト）
            body_text = page.inner_text("body")[:8000]
            metrics = scrape_metrics_from_text(body_text)
            report("dom_scrape", bool(metrics), f"matched {len(metrics)} metric keys", metrics=metrics)

            # 投稿一覧リンクらしき要素数（Studio Content）
            links = page.eval_on_selector_all(
                "a[href*='video'], a[href*='content'], a[href*='analytics']",
                "els => els.slice(0, 20).map(e => ({href: e.href, text: (e.innerText||'').trim().slice(0,80)}))",
            )
            report("post_links_sample", True, f"sample {len(links)} anchors", links=links[:5])

            return True
    except Exception as e:
        return report("playwright_cdp", False, str(e))


def scrape_metrics_from_text(text: str) -> dict:
    out = {}
    for key, pattern in METRIC_HINTS:
        m = re.search(pattern, text, re.I)
        if m:
            out[key] = m.group(1).replace(",", "")
    return out


def probe_headless_navigate(url: str) -> bool:
    """ログインなしで開けるかだけ確認（多くの場合ログイン画面にリダイレクト）。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return report("playwright_import", False, "playwright not installed")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            report("headless_navigate", True, page.url, title=page.title())
            if "login" in page.url.lower():
                report("headless_login_wall", False, "login required — VM 単体ではインサイト不可")
            body = page.inner_text("body")[:2000]
            report("headless_body_sample", True, body[:200].replace("\n", " "))
            browser.close()
            return True
    except Exception as e:
        return report("headless_navigate", False, str(e))


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe TikTok Studio browser automation feasibility")
    ap.add_argument("--cdp", default=CDP_DEFAULT, help="Chrome DevTools endpoint")
    ap.add_argument("--url", default="https://www.tiktok.com/tiktokstudio/content")
    ap.add_argument("--skip-headless", action="store_true")
    args = ap.parse_args()

    print("=== TikTok Studio browser automation probe ===", file=sys.stderr)

    ok_cdp = probe_cdp_reachable(args.cdp)
    if ok_cdp:
        probe_playwright_cdp(args.cdp, args.url)
    else:
        report(
            "cdp_skip_playwright",
            False,
            "CDP 不可のためログイン済みタブへの Playwright 接続をスキップ",
        )

    if not args.skip_headless:
        probe_headless_navigate(args.url)

    report(
        "conclusion",
        ok_cdp,
        "CDP 接続可なら Playwright 方針で進める。不可なら Browser ペインは Agent から別プロセスのため手動/CSV/スクショ",
    )
    return 0 if ok_cdp else 1


if __name__ == "__main__":
    raise SystemExit(main())
