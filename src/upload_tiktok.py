"""Publish the video to TikTok via the Content Posting API (direct FILE_UPLOAD, no
public hosting needed).

Requires TIKTOK_ACCESS_TOKEN (see auth/tiktok_get_token.py for the one-time OAuth step).

NOTE: until your TikTok developer app passes audit, posts made through this API are
only visible to you ("private/self-view" per TikTok's unaudited-client policy) -- this
is a TikTok platform restriction, not something this script can work around.
"""
import os

import requests

API = "https://open.tiktokapis.com/v2/post/publish/video/init/"


def upload_video(video_path: str, verse: dict) -> str:
    access_token = os.environ["TIKTOK_ACCESS_TOKEN"]
    video_size = os.path.getsize(video_path)

    title = (
        f'{verse["text_en"]} - {verse["surah_name_en"]} '
        f'{verse["surah_number"]}:{verse["ayah_in_surah"]} #quran #islam'
    )

    init_resp = requests.post(
        API,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "post_info": {
                "title": title[:150],
                "privacy_level": "SELF_ONLY",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            },
        },
        timeout=60,
    )
    init_resp.raise_for_status()
    payload = init_resp.json()["data"]
    upload_url = payload["upload_url"]
    publish_id = payload["publish_id"]

    with open(video_path, "rb") as f:
        video_bytes = f.read()

    put_resp = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
        },
        data=video_bytes,
        timeout=300,
    )
    put_resp.raise_for_status()
    print(f"TikTok upload submitted: publish_id {publish_id}")
    return publish_id
