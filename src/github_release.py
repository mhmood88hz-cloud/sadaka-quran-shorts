"""Publish the generated video as a GitHub Release asset to get a public, stable URL.

Instagram's Graph API requires a publicly reachable video_url (it cannot accept a raw
file upload for Reels), and this is a free way to host it without a paid CDN, as long
as the repository is public.
"""
import datetime as dt
import os

import requests

API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


def publish_video_asset(video_path: str, repo: str, token: str) -> str:
    """Create a dated release in `owner/repo` and upload video_path as an asset.

    Returns the asset's public browser_download_url.
    """
    tag = f"short-{dt.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')}"
    resp = requests.post(
        f"{API}/repos/{repo}/releases",
        headers=_headers(token),
        json={"tag_name": tag, "name": tag, "body": "Automated daily short video.", "prerelease": True},
        timeout=30,
    )
    resp.raise_for_status()
    release = resp.json()
    upload_url = release["upload_url"].split("{")[0]

    filename = os.path.basename(video_path)
    with open(video_path, "rb") as f:
        data = f.read()

    up = requests.post(
        f"{upload_url}?name={filename}",
        headers={**_headers(token), "Content-Type": "video/mp4"},
        data=data,
        timeout=120,
    )
    up.raise_for_status()
    return up.json()["browser_download_url"]
