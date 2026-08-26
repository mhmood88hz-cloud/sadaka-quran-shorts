"""Run ONCE locally to obtain a YouTube refresh token.

Prerequisites (all free):
  1. https://console.cloud.google.com -> create a project.
  2. Enable "YouTube Data API v3".
  3. OAuth consent screen -> External -> add your own Google account as a test user.
  4. Credentials -> Create OAuth client ID -> Application type "Desktop app".
  5. Download the client id/secret and paste them below via env vars or edit directly.

Run:
    python auth/youtube_get_refresh_token.py
A browser window opens for you to log in and approve. The refresh token it prints
goes into the GitHub secret YOUTUBE_REFRESH_TOKEN (client id/secret go into
YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET).
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> None:
    client_id = os.environ["YOUTUBE_CLIENT_ID"]
    client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    print("\nAdd this as GitHub secret YOUTUBE_REFRESH_TOKEN:\n")
    print(creds.refresh_token)


if __name__ == "__main__":
    main()
