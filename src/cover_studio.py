"""Suno Studio Cover Art & 10-Second Teaser Video Generator.

Generates broadcast-ready 1024x1024 album covers and 10-second MP4 video teasers:
  - Custom text overlays and typography styling
  - Reference base image ingestion from HTTP/HTTPS URLs
  - Genre-specific color grading, vinyl ring, and studio badge overlays
  - 10-second animated video teaser with Ken Burns zoom and audio synchronization
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Genre color themes: (Primary Accent, Secondary Accent, Background Core)
GENRE_PALETTES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]] = {
    "kpop": ((255, 64, 160), (0, 240, 255), (18, 12, 28)),
    "rap": ((255, 215, 0), (230, 45, 65), (14, 14, 18)),
    "metal": ((220, 20, 30), (255, 140, 0), (12, 10, 12)),
    "synthwave": ((255, 0, 128), (0, 210, 255), (10, 14, 30)),
    "rock": ((245, 120, 30), (255, 220, 100), (16, 16, 18)),
    "country": ((210, 150, 60), (250, 220, 150), (20, 16, 12)),
    "rnb": ((180, 100, 255), (255, 110, 180), (14, 12, 22)),
    "pop": ((255, 75, 140), (70, 220, 255), (16, 14, 26)),
}


def download_reference_image(url: str, dest_path: str | Path) -> Path | None:
    """Download base image from URL to be used as album cover backdrop."""
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            if len(content) > 1024:
                dest.write_bytes(content)
                return dest
    except Exception as ex:
        print(f"[!] Warning: Could not download reference image from {url}: {ex}")
    return None


def get_system_font(size: int = 36, bold: bool = True) -> ImageFont.ImageFont:
    """Try to load a clean sans-serif system font (Arial/Segoe UI/Impact), fallback to default."""
    cands = [
        "C:/Windows/Fonts/impact.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/trebucbd.ttf",
        "C:/Windows/Fonts/verdanab.ttf",
    ]
    for c in cands:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def generate_artistic_backdrop(
    size: int = 1024,
    genre: str = "pop",
    title: str = "",
) -> Image.Image:
    """Synthesize high-contrast genre-calibrated digital artwork background."""
    palette = GENRE_PALETTES.get(genre.lower(), GENRE_PALETTES["pop"])
    pri_rgb, sec_rgb, bg_rgb = palette

    img = Image.new("RGBA", (size, size), color=bg_rgb + (255,))
    draw = ImageDraw.Draw(img)

    # 1. Radial atmospheric glow
    cx, cy = size // 2, size // 2
    for r in range(size // 2, 0, -8):
        alpha = int(90 * (1.0 - r / (size // 2)))
        draw.ellipse(
            [(cx - r, cy - r), (cx + r, cy + r)],
            fill=pri_rgb + (alpha,),
        )

    # 2. Cyber / Synth / Stage Grid Lines
    grid_color = sec_rgb + (45,)
    for y in range(size // 2, size, 40):
        draw.line([(0, y), (size, y)], fill=grid_color, width=2)
    for x in range(0, size, 60):
        # Converging perspective lines towards center
        draw.line([(cx, cy + 40), (x, size)], fill=grid_color, width=2)

    # 3. Geometric frame & accents
    frame_color = pri_rgb + (180,)
    draw.rectangle([(50, 50), (size - 50, size - 50)], outline=frame_color, width=4)
    draw.rectangle([(62, 62), (size - 62, size - 62)], outline=sec_rgb + (90,), width=1)

    # Corner brackets
    b_len = 40
    for bx, by in [(50, 50), (size - 50, 50), (50, size - 50), (size - 50, size - 50)]:
        dx = b_len if bx == 50 else -b_len
        dy = b_len if by == 50 else -b_len
        draw.line([(bx, by), (bx + dx, by)], fill=sec_rgb + (255,), width=6)
        draw.line([(bx, by), (bx, by + dy)], fill=sec_rgb + (255,), width=6)

    # 4. Vinyl disc groove simulation
    for vr in range(260, 420, 24):
        draw.ellipse(
            [(cx - vr, cy - vr - 60), (cx + vr, cy + vr - 60)],
            outline=(255, 255, 255, 16),
            width=1,
        )

    return img.convert("RGBA")


def create_song_cover(
    title: str,
    *,
    artist: str = "SUNO V6 STUDIO MASTER",
    genre: str = "kpop",
    bpm: int = 122,
    custom_text: str = "",
    reference_image_url: str = "",
    image_prompt: str = "",
    out_dir: str | Path = "output/covers",
    slug: str = "",
) -> dict[str, Any]:
    """Render a complete, professional 1024x1024 album cover with custom typography overlays."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slug or re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "song"

    base_img: Image.Image | None = None

    # Step 1: Ingest reference image from URL if provided
    if reference_image_url and reference_image_url.startswith(("http://", "https://")):
        ref_path = out_dir / f"{slug}_ref_base.jpg"
        print(f"[*] Downloading reference base image: {reference_image_url} ...")
        dl_res = download_reference_image(reference_image_url, ref_path)
        if dl_res and ref_path.exists():
            try:
                raw_img = Image.open(ref_path).convert("RGBA")
                # Center crop to 1024x1024 square
                w, h = raw_img.size
                min_dim = min(w, h)
                left = (w - min_dim) // 2
                top = (h - min_dim) // 2
                cropped = raw_img.crop((left, top, left + min_dim, top + min_dim))
                base_img = cropped.resize((1024, 1024), Image.Resampling.LANCZOS)
                # Darken slightly for high typography readability
                enhancer = ImageEnhance.Brightness(base_img)
                base_img = enhancer.enhance(0.82)
                print("[+] Loaded and cropped reference base image.")
            except Exception as e:
                print(f"[!] Error processing reference image: {e}")

    # Step 2: Fallback to high-aesthetic generative backdrop
    if base_img is None:
        base_img = generate_artistic_backdrop(1024, genre=genre, title=title)

    palette = GENRE_PALETTES.get(genre.lower(), GENRE_PALETTES["pop"])
    pri_rgb, sec_rgb, _ = palette

    # Create overlay drawing context
    overlay = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Top Header Banner
    header_font = get_system_font(24, bold=True)
    header_text = f"SUNO AI STUDIO V6 // {genre.upper()} // {bpm} BPM MASTER"
    draw.text((70, 70), header_text, fill=sec_rgb + (220,), font=header_font)

    # 2. Main Title Typography with shadow & glowing drop
    title_upper = title.upper()
    title_font_size = 64 if len(title_upper) <= 16 else (50 if len(title_upper) <= 24 else 38)
    title_font = get_system_font(title_font_size, bold=True)

    title_y = 660
    # Text shadow
    for sx, sy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 4), (4, 4)]:
        draw.text((70 + sx, title_y + sy), title_upper, fill=(0, 0, 0, 240), font=title_font)
    draw.text((70, title_y), title_upper, fill=(255, 255, 255, 255), font=title_font)

    # 3. Artist / Subtitle
    sub_font = get_system_font(26, bold=False)
    sub_text = artist.upper()
    draw.text((72, title_y + title_font_size + 14), sub_text, fill=pri_rgb + (240,), font=sub_font)

    # 4. Custom User Text Overlay (if provided)
    if custom_text and custom_text.strip():
        cust_font = get_system_font(22, bold=True)
        cust_str = f"★ {custom_text.strip().upper()} ★"
        draw.rectangle([(70, title_y + title_font_size + 50), (954, title_y + title_font_size + 84)], fill=(0, 0, 0, 180))
        draw.text((82, title_y + title_font_size + 54), cust_str, fill=sec_rgb + (255,), font=cust_font)

    # 5. Parental Advisory / Studio Master Badge (Bottom Right)
    badge_x, badge_y = 780, 890
    draw.rectangle([(badge_x, badge_y), (badge_x + 180, badge_y + 70)], fill=(0, 0, 0, 220), outline=(255, 255, 255, 200), width=2)
    badge_font_lg = get_system_font(18, bold=True)
    badge_font_sm = get_system_font(12, bold=False)
    draw.text((badge_x + 12, badge_y + 8), "PARENTAL", fill=(255, 255, 255, 255), font=badge_font_lg)
    draw.text((badge_x + 12, badge_y + 28), "ADVISORY", fill=(255, 255, 255, 255), font=badge_font_lg)
    draw.text((badge_x + 12, badge_y + 48), "EXPLICIT CONTENT", fill=(255, 255, 255, 220), font=badge_font_sm)

    # 6. High-Fidelity Specs Stamp (Bottom Left)
    specs_font = get_system_font(16, bold=False)
    specs_text = "24-BIT / 96KHZ ANALOG MASTER // ZERO DIGITAL CLIPPING // CERTIFIED SUNO HIT"
    draw.text((70, 936), specs_text, fill=(200, 200, 200, 200), font=specs_font)

    # Composite layers
    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")

    png_path = out_dir / f"{slug}_cover.png"
    jpg_path = out_dir / f"{slug}_cover.jpg"
    final_img.save(png_path, "PNG")
    final_img.save(jpg_path, "JPEG", quality=95)

    # Save visual AI prompt for Midjourney / DALL-E / Flux
    default_prompt = (
        f"Award-winning album cover art for '{title}', {genre} music style, "
        f"aesthetic cinematic lighting, vibrant pastel and electric neon highlights, "
        f"hyper-detailed 8k resolution, trending on ArtStation, album typography"
    )
    prompt_file = out_dir / f"{slug}_cover_prompt.txt"
    final_prompt = image_prompt or default_prompt
    prompt_file.write_text(final_prompt, encoding="utf-8")

    print(f"[+] Album Cover Art Generated:")
    print(f"    PNG: {png_path} ({png_path.stat().st_size // 1024} KB)")
    print(f"    JPG: {jpg_path} ({jpg_path.stat().st_size // 1024} KB)")
    print(f"    AI Prompt: {prompt_file}")

    return {
        "png_path": png_path,
        "jpg_path": jpg_path,
        "prompt_path": prompt_file,
        "prompt": final_prompt,
    }


def generate_10s_teaser_video(
    cover_image_path: str | Path,
    out_video_path: str | Path,
    *,
    audio_path: str | Path | None = None,
    bpm: int = 122,
    title: str = "",
) -> Path | None:
    """Generate a broadcast-ready 10-second MP4 video teaser with dynamic Ken Burns zoom and audio beat."""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        print("[!] ffmpeg not found in PATH; skipping video generation.")
        return None

    cover = Path(cover_image_path)
    if not cover.exists():
        print(f"[!] Cover image not found: {cover}")
        return None

    out_video = Path(out_video_path)
    out_video.parent.mkdir(parents=True, exist_ok=True)

    print(f"[*] Rendering 10-Second Video Teaser: {out_video.name} ...")

    # If audio exists, use first 10 seconds. Otherwise synthesize a rhythmic 10s electronic audio pulse.
    has_real_audio = audio_path and Path(audio_path).exists()
    audio_input_args = ["-ss", "0", "-t", "10", "-i", str(audio_path)] if has_real_audio else [
        "-f", "lavfi", "-t", "10",
        "-i", f"sine=frequency=110:duration=10"
    ]

    # Video filter: Smooth Ken Burns slow-zoom over 10 seconds (250 frames at 25fps)
    vf_filter = "zoompan=z='min(zoom+0.0012,1.14)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=250:s=1080x1080:fps=25"

    cmd = [
        ffmpeg_bin, "-y",
        "-loop", "1", "-t", "10", "-i", str(cover),
        *audio_input_args,
        "-vf", vf_filter,
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-shortest",
        str(out_video)
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode == 0 and out_video.exists():
            vsize = out_video.stat().st_size // 1024
            print(f"[+] 10-Second Teaser Video Created: {out_video} ({vsize} KB)")
            return out_video
        else:
            print(f"[!] ffmpeg error rendering teaser video: {res.stderr[-300:]}")
    except Exception as ex:
        print(f"[!] Video generation failed: {ex}")
    return None
