"""Weekly pipeline entry point (local or Cloud Automation).

  python run_weekly.py              # analyze + write report skeleton
  python run_weekly.py --merge       # sync results.csv rows from registry
  python run_weekly.py --render      # also run build_batch + make_registry (needs SRC)

Exit codes:
  0  OK (report written)
  2  Need TikTok metrics (results empty)
  1  Error
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

from config import REPORTS, SRC
from analyze_results import compute_analysis, write_report

ROOT = Path(__file__).resolve().parent


def main():
    merge = "--merge" in sys.argv
    do_render = "--render" in sys.argv

    if merge:
        subprocess.run([sys.executable, "update_results.py", "--merge", "registry"], check=True, cwd=ROOT)

    report_path = REPORTS / f"{date.today().isoformat()}_weekly.md"
    REPORTS.mkdir(parents=True, exist_ok=True)

    data = compute_analysis()
    if data is None:
        print("results.csv がありません。Automation Step 1 で TikTok Studio から取得してください。")
        subprocess.run([sys.executable, "update_results.py", "--merge", "registry"], cwd=ROOT)
        sys.exit(2)

    write_report(data, str(report_path))
    if not data["rows"]:
        print("有効な metrics がありません（views>0 が必要）。レポート骨子のみ作成しました。")
        sys.exit(2)

    if do_render:
        if not SRC.is_file():
            print(f"元動画がありません: {SRC}  （SETROUNDLY_SRC を設定）")
            sys.exit(1)
        subprocess.run([sys.executable, "build_batch.py"], cwd=ROOT, check=True)
        subprocess.run([sys.executable, "make_registry.py"], cwd=ROOT, check=True)
        print("render + registry 完了")

    print(f"\n週次完了 → {report_path}")
    print("次: 競合リサーチメモをレポート §3–4 に追記し、build_batch の VIDEOS を勝ち型寄りに更新。")
    sys.exit(0)


if __name__ == "__main__":
    main()
