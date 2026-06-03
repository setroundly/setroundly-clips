"""Paths for SETROUNDLY_clips only (not iam-pro / other repos)."""
from pathlib import Path
import os
import shutil

ROOT = Path(__file__).resolve().parent
DESKTOP = ROOT.parent

# Live source stays on Desktop (too large for Git). Override with env SETROUNDLY_SRC.
_default_src = DESKTOP / "2026-05-29 SETROUNDLY.mp4"
SRC = Path(os.environ.get("SETROUNDLY_SRC", _default_src))

_winget_ffmpeg = Path(
    os.environ.get(
        "LOCALAPPDATA",
        r"C:\Users\jun19\AppData\Local",
    )
) / (
    "Microsoft/WinGet/Packages/"
    "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
    "ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"
)


def resolve_ffmpeg() -> str:
    if os.environ.get("FFMPEG"):
        return os.environ["FFMPEG"]
    if _winget_ffmpeg.is_file():
        return str(_winget_ffmpeg)
    found = shutil.which("ffmpeg")
    if found:
        return found
    return "ffmpeg"


FFMPEG = resolve_ffmpeg()
REPORTS = ROOT / "reports"
