"""Shared schema for TikTok post insights (results.csv)."""

RESULT_FIELDS = [
    "date",
    "video_id",
    "title",
    "views",
    "likes",
    "comments",
    "shares",
    "saves",
    "avg_watch_time",
    "full_watch_rate",
    "two_sec_retention",
    "five_sec_retention",
    "retention_notes",
]

RES = "results.csv"
TPL = "results_template.csv"
POSTS = "tiktok_posts.csv"
REG = "registry.csv"

EMPTY_MARKERS = {"", "取得不可", "N/A", "n/a", "-", "—", "不明"}
