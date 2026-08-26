"""Render a vertical (1080x1920) short video for a given verse dict from fetch_verse.pick_verse()."""
import textwrap
from pathlib import Path

import arabic_reshaper
import numpy as np
import requests
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# moviepy 1.0.3 references the Pillow<10 constant removed in newer Pillow.
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "assets" / "fonts"
OUTPUT_DIR = ROOT / "output"

W, H = 1080, 1920
FPS = 30
MAX_DURATION = 90  # keep well inside Shorts/Reels/TikTok short-form limits


def _download_audio(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


def _make_background() -> Image.Image:
    """Calm night-sky gradient with soft stars. No external images needed -> no copyright risk."""
    top = np.array([9, 20, 38])
    bottom = np.array([2, 6, 14])
    gradient = np.linspace(0, 1, H).reshape(H, 1, 1)
    img_arr = (top * (1 - gradient) + bottom * gradient).astype(np.uint8)
    img_arr = np.repeat(img_arr, W, axis=1)
    img = Image.fromarray(img_arr, "RGB")

    draw = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(42)
    for _ in range(160):
        x, y = rng.integers(0, W), rng.integers(0, H)
        r = rng.choice([1, 1, 1, 2])
        alpha = int(rng.integers(60, 180))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, alpha))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((W * 0.2, H * 0.15, W * 0.8, H * 0.55), fill=(80, 120, 170, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    return img


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list:
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_centered_lines(draw, lines, font, y, max_width, fill, line_spacing=1.35, rtl=False):
    line_height = font.size * line_spacing
    for i, line in enumerate(lines):
        w = draw.textlength(line, font=font)
        x = (max_width - w) / 2
        draw.text((x, y + i * line_height), line, font=font, fill=fill)
    return y + len(lines) * line_height


def _wrap_arabic_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list:
    """Wrap Arabic text into lines, keeping logical (reading) word order while wrapping,
    then apply bidi reordering per finished line -- reordering the whole text up front
    before wrapping scrambles which words land on which line."""
    words = [arabic_reshaper.reshape(w) for w in text.split()]
    lines, current = [], []
    for word in words:
        trial = current + [word]
        if draw.textlength(" ".join(trial), font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = [word]
    if current:
        lines.append(current)
    return [get_display(" ".join(line_words)) for line_words in lines]


def _make_frame(verse: dict) -> Image.Image:
    img = _make_background().convert("RGBA")
    draw = ImageDraw.Draw(img)

    # BASIC layout engine: we already reshape/reorder the Arabic ourselves, and letting
    # Pillow's raqm engine (when available, e.g. on Linux CI) shape it a second time
    # garbles the text -- BASIC draws glyphs as given, with no engine involved.
    arabic_font = ImageFont.truetype(str(FONTS_DIR / "Amiri-Bold.ttf"), 76, layout_engine=ImageFont.Layout.BASIC)
    en_font = ImageFont.truetype(str(FONTS_DIR / "Poppins-Regular.ttf"), 40)
    de_font = ImageFont.truetype(str(FONTS_DIR / "Poppins-Regular.ttf"), 36)
    attribution_font = ImageFont.truetype(str(FONTS_DIR / "Poppins-Medium.ttf"), 32)

    margin = 90
    content_w = W - 2 * margin

    arabic_lines = _wrap_arabic_lines(verse["text_ar"], arabic_font, content_w, draw)

    en_lines = textwrap.wrap(f'"{verse["text_en"]}"', width=34)
    de_lines = textwrap.wrap(f'"{verse["text_de"]}"', width=38)

    y = H * 0.30
    y = _draw_centered_lines(draw, arabic_lines, arabic_font, y, W, (255, 250, 235, 255), rtl=True)
    y += 50

    y = _draw_centered_lines(draw, en_lines, en_font, y, W, (225, 225, 235, 255))
    y += 30
    y = _draw_centered_lines(draw, de_lines, de_font, y, W, (190, 195, 210, 255))

    attribution = f'{verse["surah_name_en"]} {verse["surah_number"]}:{verse["ayah_in_surah"]}'
    attrib_w = draw.textlength(attribution, font=attribution_font)
    draw.text(((W - attrib_w) / 2, H - 160), attribution, font=attribution_font, fill=(160, 170, 190, 255))

    return img.convert("RGB")


def build_video(verse: dict, out_name: str = "short.mp4") -> Path:
    from moviepy.editor import AudioFileClip, ImageClip

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = OUTPUT_DIR / "verse_audio.mp3"
    _download_audio(verse["audio_url"], audio_path)

    audio_clip = AudioFileClip(str(audio_path))
    duration = min(audio_clip.duration, MAX_DURATION)
    audio_clip = audio_clip.subclip(0, duration)

    frame = _make_frame(verse)
    frame_path = OUTPUT_DIR / "frame.png"
    frame.save(frame_path)

    def zoom(t):
        # slow Ken Burns zoom, 1.0 -> 1.08 over the clip
        return 1.0 + 0.08 * (t / duration)

    clip = ImageClip(str(frame_path)).set_duration(duration).resize(zoom)
    clip = clip.set_position(("center", "center")).resize(height=int(H * 1.1))
    clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=W, height=H)
    clip = clip.set_audio(audio_clip)

    out_path = OUTPUT_DIR / out_name
    clip.write_videofile(
        str(out_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        bitrate="6000k",
    )
    return out_path


if __name__ == "__main__":
    import json
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from fetch_verse import pick_verse

    v = pick_verse()
    print(json.dumps(v, ensure_ascii=False, indent=2))
    path = build_video(v)
    print("wrote", path)
