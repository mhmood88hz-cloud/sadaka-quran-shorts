"""Fetch a random, previously-unused Quran verse (Arabic + EN + DE + recitation audio)."""
import json
import os
import random
from pathlib import Path

import requests

API_BASE = "https://api.alquran.cloud/v1/ayah"
# Change RECITER to any audio edition identifier from
# https://api.alquran.cloud/v1/edition/format/audio (e.g. ar.alafasy, ar.husary).
RECITER = os.environ.get("RECITER_EDITION", "ar.abdurrahmaansudais")
TOTAL_AYAHS = 6236

STATE_FILE = Path(__file__).resolve().parent.parent / "state" / "used_verses.json"


def _load_used() -> set:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    return set()


def _save_used(used: set) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(sorted(used)), encoding="utf-8")


def pick_verse() -> dict:
    used = _load_used()
    available = [n for n in range(1, TOTAL_AYAHS + 1) if n not in used]
    if not available:
        used = set()
        available = list(range(1, TOTAL_AYAHS + 1))

    ayah_number = random.choice(available)
    editions = f"quran-uthmani,en.sahih,de.bubenheim,{RECITER}"
    resp = requests.get(f"{API_BASE}/{ayah_number}/editions/{editions}", timeout=30)
    resp.raise_for_status()
    data = resp.json()["data"]

    by_edition = {e["edition"]["identifier"]: e for e in data}
    arabic = by_edition["quran-uthmani"]
    english = by_edition["en.sahih"]
    german = by_edition["de.bubenheim"]
    audio = by_edition[RECITER]

    verse = {
        "ayah_number": ayah_number,
        "surah_name_en": arabic["surah"]["englishName"],
        "surah_name_ar": arabic["surah"]["name"],
        "surah_number": arabic["surah"]["number"],
        "ayah_in_surah": arabic["numberInSurah"],
        "text_ar": arabic["text"],
        "text_en": english["text"],
        "text_de": german["text"],
        "audio_url": audio["audio"],
    }

    used.add(ayah_number)
    _save_used(used)
    return verse


if __name__ == "__main__":
    v = pick_verse()
    print(json.dumps(v, ensure_ascii=False, indent=2))
