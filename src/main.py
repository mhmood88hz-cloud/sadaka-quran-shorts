"""Daily entry point: pick a verse, render the short video, publish to every platform
for which credentials are present in the environment. Missing credentials for a
platform simply skip that platform (so you can enable them one at a time)."""
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_video import build_video
from download_fonts import ensure_fonts
from fetch_verse import pick_verse


def _try(label: str, fn) -> None:
    try:
        fn()
        print(f"[ok] {label}")
    except Exception:
        print(f"[FAILED] {label}")
        traceback.print_exc()


def main() -> None:
    ensure_fonts()
    verse = pick_verse()
    print(f"Selected verse: {verse['surah_name_en']} {verse['surah_number']}:{verse['ayah_in_surah']}")

    video_path = build_video(verse)
    print(f"Video rendered: {video_path}")

    if os.environ.get("YOUTUBE_REFRESH_TOKEN"):
        from upload_youtube import upload_short
        _try("YouTube upload", lambda: upload_short(str(video_path), verse))
    else:
        print("[skip] YouTube: no YOUTUBE_REFRESH_TOKEN set")

    if os.environ.get("IG_ACCESS_TOKEN"):
        from upload_instagram import upload_reel
        _try("Instagram upload", lambda: upload_reel(str(video_path), verse))
    else:
        print("[skip] Instagram: no IG_ACCESS_TOKEN set")

    if os.environ.get("TIKTOK_ACCESS_TOKEN"):
        from upload_tiktok import upload_video
        _try("TikTok upload", lambda: upload_video(str(video_path), verse))
    else:
        print("[skip] TikTok: no TIKTOK_ACCESS_TOKEN set")


if __name__ == "__main__":
    main()
