"""Download open-license (OFL) fonts needed for rendering, if not already present."""
from pathlib import Path

import requests

FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

FONTS = {
    "Amiri-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Regular.ttf",
    "Amiri-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Bold.ttf",
    "Poppins-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf",
    "Poppins-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-Medium.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Medium.ttf",
}


def ensure_fonts() -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in FONTS.items():
        dest = FONTS_DIR / filename
        if dest.exists() and dest.stat().st_size > 0:
            continue
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        print(f"downloaded {filename}")


if __name__ == "__main__":
    ensure_fonts()
