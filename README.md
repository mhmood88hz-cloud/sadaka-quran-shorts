# Sadaka — Automated Daily Quran Shorts

Generates a short vertical video (Arabic verse + English/German translation + recitation
audio, over a generated background) for a random, not-yet-used ayah every day, and
publishes it to YouTube Shorts, Instagram Reels, and TikTok. Runs entirely on free
tiers — no paid subscriptions, no paid APIs.

## How it works

- `src/fetch_verse.py` — picks a random unused ayah (tracked in `state/used_verses.json`)
  from the free [alquran.cloud](https://alquran.cloud) API: Arabic text, English (Sahih
  International) and German (Bubenheim & Elyas) translations, and a recitation audio URL.
- `src/build_video.py` — renders a 1080x1920 video: a generated (copyright-free) night-sky
  background with a slow zoom, the verse text in Arabic/English/German, and the
  recitation audio.
- `src/upload_youtube.py`, `src/upload_instagram.py`, `src/upload_tiktok.py` — publish the
  finished video to each platform. Each is skipped automatically if its credentials
  aren't set, so you can enable platforms one at a time.
- `.github/workflows/daily-video.yml` — runs the whole pipeline once a day for free on
  GitHub Actions (public repos get unlimited free Action minutes).

## One-time setup

### 0. Push this project to a **public** GitHub repository

Instagram's API needs a public URL to fetch the video from, which this project gets for
free via GitHub Releases — that only works if the repo is public.

```bash
git init
git add .
git commit -m "Initial commit"
gh repo create sadaka-quran-shorts --public --source=. --push
```

### 1. Reciter (optional)

Default is Abdurrahman As-Sudais. To change it, set the repo variable `RECITER_EDITION`
(Settings → Secrets and variables → Actions → Variables) to any audio edition id from
https://api.alquran.cloud/v1/edition/format/audio (e.g. `ar.alafasy`, `ar.husary`).

### 2. YouTube Shorts (free)

1. https://console.cloud.google.com → new project.
2. Enable **YouTube Data API v3** (APIs & Services → Library).
3. OAuth consent screen → External → add your own Google account under "Test users".
4. Credentials → Create OAuth client ID → type **Desktop app**. Note the client id/secret.
5. Locally:
   ```bash
   set YOUTUBE_CLIENT_ID=xxx
   set YOUTUBE_CLIENT_SECRET=xxx
   python auth/youtube_get_refresh_token.py
   ```
   Approve in the browser that opens. Copy the printed refresh token.
6. Add GitHub secrets: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`.

### 3. Instagram Reels (free, needs a Business/Creator account)

1. Convert your Instagram account to a **Professional (Business or Creator)** account
   in the Instagram app, and connect it to a Facebook Page (required by Meta).
2. https://developers.facebook.com → create an app (type "Business").
3. Add product **Instagram Graph API**.
4. Use the [Graph API Explorer](https://developers.facebook.com/tools/explorer/) with
   your app to generate a **long-lived Page access token** with the
   `instagram_content_publish`, `pages_show_list`, and `instagram_basic` permissions
   (Meta's docs: [long-lived tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens#get-a-long-lived-user-access-token)).
5. Find your Instagram Business Account ID via
   `GET /me/accounts` then `GET /{page-id}?fields=instagram_business_account`.
6. Add GitHub secrets: `IG_ACCESS_TOKEN`, `IG_BUSINESS_ACCOUNT_ID`.

Meta's long-lived tokens expire after ~60 days — you'll need to refresh it periodically
(a reminder in your calendar is enough for a hobby project like this).

### 4. TikTok (free, but capped until app review)

1. https://developers.tiktok.com → register an app, add product **Content Posting API**.
2. Add redirect URI `http://localhost:8722/callback`.
3. Locally:
   ```bash
   set TIKTOK_CLIENT_KEY=xxx
   set TIKTOK_CLIENT_SECRET=xxx
   python auth/tiktok_get_token.py
   ```
   Approve in the browser. Copy the printed access token.
4. Add GitHub secret `TIKTOK_ACCESS_TOKEN`.

**Important limitation:** until TikTok reviews and approves your developer app, videos
posted via the API are only visible to you (`SELF_ONLY`), not publicly — this is a
TikTok platform restriction. Submit your app for audit in the TikTok developer portal
once you're happy with the output to make posts public.

Also note: TikTok access tokens expire after ~24 hours and need refreshing — this repo
does not yet automate the refresh step, so TikTok publishing will need the token
re-generated periodically (or extend `upload_tiktok.py` to use the refresh_token TikTok
also issues).

### 5. Enable the schedule

Once the secrets you want are in place, the workflow runs automatically every day at
08:00 UTC. You can also trigger it manually: repo → Actions → "Daily Quran Short" →
Run workflow.

## Local test run

```bash
pip install -r requirements.txt
python src/build_video.py   # generates output/short.mp4 without publishing anywhere
python src/main.py          # full pipeline; only publishes to platforms with secrets set as env vars
```

## Costs

Everything used is a free tier: GitHub Actions (public repo), alquran.cloud API,
Google Cloud OAuth + YouTube Data API, Meta Graph API, TikTok Content Posting API,
Google Fonts (Amiri, Poppins — OFL licensed). No subscriptions.
