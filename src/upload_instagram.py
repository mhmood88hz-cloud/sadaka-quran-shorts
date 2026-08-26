"""Publish the video as an Instagram Reel via the Graph API.

Requires:
  - IG_BUSINESS_ACCOUNT_ID  (the Instagram professional account's numeric ID)
  - IG_ACCESS_TOKEN         (long-lived Page access token with instagram_content_publish)
  - GITHUB_TOKEN + GITHUB_REPOSITORY (used to host the mp4 publicly, see github_release.py)

Graph API cannot accept a raw file upload for Reels -- it needs a public video_url,
which is why the video is first pushed to a GitHub Release asset.
"""
import os
import time

import requests

GRAPH = "https://graph.facebook.com/v20.0"


def upload_reel(video_path: str, verse: dict) -> str:
    from github_release import publish_video_asset

    video_url = publish_video_asset(
        video_path,
        repo=os.environ["GITHUB_REPOSITORY"],
        token=os.environ["GITHUB_TOKEN"],
    )

    ig_user_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    caption = (
        f'{verse["text_en"]}\n\n{verse["surah_name_en"]} '
        f'({verse["surah_number"]}:{verse["ayah_in_surah"]})\n\n#quran #islam #reels'
    )

    create = requests.post(
        f"{GRAPH}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=60,
    )
    create.raise_for_status()
    container_id = create.json()["id"]

    status = "IN_PROGRESS"
    for _ in range(30):
        time.sleep(10)
        check = requests.get(
            f"{GRAPH}/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=30,
        )
        check.raise_for_status()
        status = check.json()["status_code"]
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError("Instagram failed to process the video container")
    else:
        raise TimeoutError("Instagram container never finished processing")

    publish = requests.post(
        f"{GRAPH}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token},
        timeout=60,
    )
    publish.raise_for_status()
    media_id = publish.json()["id"]
    print(f"Instagram Reel published: media id {media_id}")
    return media_id
