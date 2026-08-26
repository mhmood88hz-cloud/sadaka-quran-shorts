"""Run ONCE locally to obtain a TikTok access token.

Prerequisites (all free):
  1. https://developers.tiktok.com -> register an app.
  2. Add product "Content Posting API".
  3. Add redirect URI: http://localhost:8722/callback
  4. Note your client_key / client_secret.

Set env vars TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, then run:
    python auth/tiktok_get_token.py
It opens a login URL for you to approve in your browser, catches the redirect on a
local server, and prints the access token to store as GitHub secret TIKTOK_ACCESS_TOKEN.

NOTE: TikTok access tokens expire (~24h) and must be refreshed with the refresh_token
this script also prints; the daily workflow expects TIKTOK_ACCESS_TOKEN to already be
valid, so re-run this (or wire in a refresh step) if it lapses.
"""
import os
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

REDIRECT_URI = "http://localhost:8722/callback"
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

_auth_code = {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in qs:
            _auth_code["code"] = qs["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorized. You can close this tab.")
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, *args):
        pass


def main() -> None:
    client_key = os.environ["TIKTOK_CLIENT_KEY"]
    client_secret = os.environ["TIKTOK_CLIENT_SECRET"]

    params = {
        "client_key": client_key,
        "scope": "video.publish",
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": "sadaka",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print(f"Opening browser for TikTok login:\n{url}\n")
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8722), _Handler)
    while "code" not in _auth_code:
        server.handle_request()

    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": _auth_code["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    print("\nAdd this as GitHub secret TIKTOK_ACCESS_TOKEN:\n")
    print(data["access_token"])
    print("\nRefresh token (save somewhere safe):\n")
    print(data.get("refresh_token"))


if __name__ == "__main__":
    main()
