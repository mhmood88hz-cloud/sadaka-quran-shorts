"""Upload the generated video to YouTube as a Short.

Requires a one-time OAuth authorization (see auth/youtube_get_refresh_token.py) whose
resulting refresh token is stored as the GitHub secret YOUTUBE_REFRESH_TOKEN, alongside
YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET from a free Google Cloud OAuth client.
"""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials() -> Credentials:
    return Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def upload_short(video_path: str, verse: dict) -> str:
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    title = f'{verse["surah_name_en"]} {verse["surah_number"]}:{verse["ayah_in_surah"]} #Shorts'
    description = (
        f'{verse["text_en"]}\n\n{verse["text_de"]}\n\n'
        f'{verse["surah_name_en"]} ({verse["surah_number"]}:{verse["ayah_in_surah"]})\n'
        f"#Quran #Islam #Shorts"
    )

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": ["Quran", "Islam", "Shorts"],
            "categoryId": "22",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    video_id = response["id"]
    print(f"YouTube Short published: https://youtube.com/shorts/{video_id}")
    return video_id


if __name__ == "__main__":
    import sys

    upload_short(sys.argv[1], {"surah_name_en": "Test", "surah_number": 1, "ayah_in_surah": 1, "text_en": "", "text_de": ""})
