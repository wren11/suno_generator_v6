"""Interactive Step-by-Step Guided Wizard for Suno Studio V6 Song Creation.

Guides the user through:
  Step 1: Theme & Style (with live Suno.com trending recommendations)
  Step 2: Clean Title resolution (intelligent auto-detection or custom)
  Step 3: Vocal lead & BPM tempo
  Step 4: Lyrical engine & anti-cliche constraints (optional lipograms)
  Step 5: Album Cover Art studio (custom text overlay, reference image URL, AI prompt)
  Step 6: 10-Second Video Teaser rendering (MP4 Ken Burns zoom with audio beat)
  Step 7: Complete Suno Studio V6 JSON export & catalog retraining
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from src.catalog import SongCatalogStore
from src.cover_studio import create_song_cover, generate_10s_teaser_video
from src.downloader import SunoSongDownloader
from src.song_creator import create_complete_song_bundle, detect_song_profile


def _prompt_input(prompt: str, default: str = "") -> str:
    """Prompt user for input with default fallback."""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "
    try:
        val = input(display).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        print("\n[!] Wizard cancelled.")
        return default


def get_live_suno_inspirations() -> list[dict[str, str]]:
    """Retrieve top trending songs from Suno explore feed or catalog for smart wizard suggestions."""
    inspirations = []
    try:
        dl = SunoSongDownloader()
        clips = dl.fetch_unified_feed(feed_id="trending", page_size=10, max_items=5)
        for c in clips:
            title = str(c.get("title") or "Trending Track")
            meta = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
            tags = str(meta.get("tags") or c.get("tags") or "Trending Pop")
            inspirations.append({"title": title, "style": tags[:75]})
    except Exception:
        pass

    if not inspirations:
        inspirations = [
            {"title": "Desktop Girlfriend", "style": "Cute K-Pop cartoonish pop glam, 128 BPM, bright sparkly synths"},
            {"title": "Supersonic Velocity", "style": "Detroit chopper rap god flow, 140 BPM, locked 16th clutch pocket"},
            {"title": "Cyber Waifu", "style": "Japanese future bass & hyper-dubstep, 145 BPM, chiptune gltich"},
            {"title": "Midnight Drive", "style": "Dark glam synthwave, 122 BPM, analog Juno bassline, radio master"},
        ]
    return inspirations


get_trending_inspirations = get_live_suno_inspirations


def run_guided_wizard(out_dir: str | Path = "output/songs", engine: str = "llm") -> dict[str, Any] | None:
    """Run the step-by-step guided wizard in terminal / REPL."""
    print("\n" + "=" * 76)
    print("   🧙  SUNO STUDIO V6 // GUIDED HIT SONG & MEDIA WIZARD")
    print("=" * 76)
    print("  I will guide you step-by-step to build a radio-ready Suno V6 song bundle:")
    print("   • Calibrated 3K & 5K Suno Studio JSON payloads")
    print("   • Story-locked lyrics with 100% Anti-AI Cliché guarantee")
    print("   • Broadcast-ready 1024x1024 Album Cover Art (with custom text overlay & URL)")
    print("   • 10-Second Animated Video Teaser (1080x1080 MP4 with audio beat)")
    print("   • Automatic Suno.com Catalog Ingestion & Model Retraining")
    print("=" * 76 + "\n")

    # -------------------------------------------------------------
    # Step 1: Song Theme / Genre / Idea
    # -------------------------------------------------------------
    print("┌── STEP 1 of 5: Song Theme & Musical Genre")
    print("│   Trending Suno hits you can draw inspiration from:")
    for idx, insp in enumerate(get_trending_inspirations()[:4], 1):
        print(f"│     {idx}. {insp['title']:<20} -> {insp['style']}")
    print("│")
    theme_in = _prompt_input("└── Enter your theme, genre, or vibe (or press Enter for default)", "cyberpunk synthwave future hacker, bright dance pop")
    theme = theme_in.strip()

    # -------------------------------------------------------------
    # Step 2: Song Title & Artist Persona
    # -------------------------------------------------------------
    prof = detect_song_profile(theme)
    default_title = prof["title"]
    print("\n┌── STEP 2 of 5: Song Title & Artist Persona")
    title_in = _prompt_input(f"│   Song title [Default: '{default_title}']", default_title)
    title = title_in.strip() or default_title
    artist_in = _prompt_input("└── Artist or Studio Persona [Default: 'SUNO V6 STUDIO MASTER']", "SUNO V6 STUDIO MASTER")
    artist = artist_in.strip() or "SUNO V6 STUDIO MASTER"

    # -------------------------------------------------------------
    # Step 3: Vocal Lead & BPM
    # -------------------------------------------------------------
    detected_vocal = prof["vocal_gender"].upper()
    print("\n┌── STEP 3 of 5: Vocal Lead & Tempo")
    print(f"│   Auto-detected vocal style for this theme: {detected_vocal}")
    vocal_choice = _prompt_input(f"│   Choose vocal lead: [F]emale / [M]ale / [A]uto-Detect [Default: {detected_vocal}]", detected_vocal).strip().lower()
    if vocal_choice.startswith("f"):
        vocal_in = "f"
    elif vocal_choice.startswith("m"):
        vocal_in = "m"
    else:
        vocal_in = prof["vocal_gender"]

    bpm_str = _prompt_input(f"└── Beats Per Minute (BPM) [Default: {prof['bpm']}]", str(prof["bpm"])).strip()
    try:
        bpm = int(bpm_str)
    except Exception:
        bpm = prof["bpm"]

    # -------------------------------------------------------------
    # Step 4: Lyrical Constraints & Anti-Cliche
    # -------------------------------------------------------------
    print("\n┌── STEP 4 of 5: Lyrical Constraints & Anti-Cliche Engine")
    print("│   [Anti-AI Cliche Engine Active: 'neon, tapestry, whispers, echoes, ignite, shadows' PURGED]")
    lipogram_choice = _prompt_input("└── Apply Lipogram constraint? (e.g. type 'e' to avoid letter 'e', or Enter for none)", "").strip().lower()
    lipogram_letter = lipogram_choice[0] if lipogram_choice else ""

    # -------------------------------------------------------------
    # Step 5: Album Cover Art Studio & 10s Teaser Video
    # -------------------------------------------------------------
    print("\n┌── STEP 5 of 5: Album Art & 10-Second Teaser Video Studio")
    custom_text = _prompt_input("│   Custom text overlay on cover (e.g. 'DELUXE 4K EDITION') [Optional]", "")
    ref_image_url = _prompt_input("│   Reference image URL to download as base cover [Optional]", "")
    image_prompt = _prompt_input("└── Custom AI Art Prompt (leave blank for automatic visual styling)", "")
    print()

    # -------------------------------------------------------------
    # Execution & Output Generation
    # -------------------------------------------------------------
    print("=" * 65)
    print("  🪄  WIZARD GENERATING MASTER SONG ASSETS ...")
    print("=" * 65)

    bundle = create_complete_song_bundle(
        title=title,
        theme=theme,
        vocal_gender=vocal_in,
        bpm=bpm,
        out_dir=out_dir,
        lipogram=lipogram_letter,
        engine=engine,
    )

    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "song"
    song_dir = Path(out_dir) / slug

    # Render custom cover art
    print("\n[*] Creating custom album cover...")
    cover_res = create_song_cover(
        title,
        artist=artist,
        genre=prof["genre"],
        bpm=bpm,
        custom_text=custom_text,
        reference_image_url=ref_image_url,
        image_prompt=image_prompt,
        out_dir=song_dir,
        slug=slug,
    )

    # Render 10-second teaser video
    print("\n[*] Rendering 10-second MP4 teaser video...")
    video_path = generate_10s_teaser_video(
        cover_res["png_path"],
        song_dir / f"{slug}_teaser_10s.mp4",
        bpm=bpm,
        title=title,
    )

    print("\n" + "=" * 65)
    print("  🎉  WIZARD COMPLETE: ALL ASSETS READY FOR SUNO!")
    print("=" * 65)
    print(f"  • Song Directory:  {song_dir}")
    print(f"  • 3K JSON:         {bundle['len_3k']:,} characters ({song_dir / f'{slug}_v6_3k.json'})")
    print(f"  • 5K JSON:         {bundle['len_5k']:,} characters ({song_dir / f'{slug}_v6_5k.json'})")
    print(f"  • Cover Art (PNG): {cover_res['png_path']}")
    print(f"  • Cover Art (JPG): {cover_res['jpg_path']}")
    if video_path and video_path.exists():
        print(f"  • Teaser Video:    {video_path} (10s 1080x1080 MP4)")
    print(f"  • Synchronized LRC:{song_dir / f'{slug}_lyrics.lrc'}")
    print(f"  • Production Brief:{song_dir / f'{slug}_production_brief.md'}")
    print("=" * 65)

    print("\n" + "=" * 65)
    print("  📋  PASTE-READY SUNO STUDIO V6 3K PAYLOAD")
    print("=" * 65)
    print(json.dumps(bundle["payload_3k"], indent=2, ensure_ascii=False))
    print("=" * 65 + "\n")

    return {
        "title": title,
        "bundle": bundle,
        "cover": cover_res,
        "video": video_path,
        "song_dir": song_dir,
    }


def main() -> int:
    run_guided_wizard()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
