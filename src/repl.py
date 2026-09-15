"""Interactive REPL harness for Suno prompt generation, model inspection, and song ingestion."""

from __future__ import annotations

import cmd
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

from src.catalog import SongCatalogStore
from src.inference import SongwritingReferenceModel
from src.keywords import KeywordStyleAnalytics
from src.trainer import train_from_url

try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BANNER = r"""
======================================================================
  ____  _   _ _   _  ___     ____ _____ _   _ _____ ____     _  _____ ___  ____  
 / ___|| | | | \ | |/ _ \   / ___| ____| \ | | ____|  _ \   / \|_   _/ _ \|  _ \ 
 \___ \| | | |  \| | | | | | |  _|  _| |  \| |  _| | |_) | / _ \ | || | | | |_) |
  ___) | |_| | |\  | |_| | | |_| | |___| |\  | |___|  _ < / ___ \| || |_| |  _ < 
 |____/ \___/|_| \_|\___/   \____|_____|_| \_|_____|_| \_/_/   \_\_| \___/|_| \_\

  Suno AI Studio V6 Song Generator & Guided Media Engine
======================================================================
  🧙 Type 'wizard'   - Step-by-step guided creator (holds your hand!)
  🎵 Type 'song'     - Create complete hit song + cover art + 10s video
  🔥 Type 'trending' - Fetch live Suno.com explore hits or train model
  💡 Type 'suggest'  - Real-time style suggestions from live catalog
  ❓ Type 'help'     - View all interactive commands
======================================================================
"""


class SunoReplHarness(cmd.Cmd):
    intro = BANNER
    prompt = "suno> "

    def __init__(
        self,
        catalog_path: str | Path = "models/suno_song_catalog.json",
        inference_path: str | Path = "models/suno_song_inference_model.json",
        prompts_dir: str | Path = "output/prompts",
    ) -> None:
        super().__init__()
        self.catalog_path = Path(catalog_path)
        self.inference_path = Path(inference_path)
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        self.cmd_history: list[str] = []
        self.history_file = Path(".suno_repl_history")
        if readline and self.history_file.exists():
            try:
                readline.read_history_file(str(self.history_file))
            except Exception:
                pass

        self.catalog = SongCatalogStore(self.catalog_path)
        self.model = SongwritingReferenceModel(self.inference_path)


    def do_stats(self, arg: str) -> None:
        """Display dataset, vocabulary, and inference model statistics."""
        print(self.catalog.format_stats_report())
        print(self.model.format_report())

    def do_v6(self, arg: str) -> None:
        """Generate Suno Studio V6 JSON configuration (with Scansion-LM lyrics + MAX audio quality).
        Usage: v6 [theme] [--title "Title"] [--gender f|m] [--mode 3k|5k|both] [--assets]
        Example: v6 "dark glam electropop" --title "New Name on the Door" --gender f --mode both
        """
        from src.llm import generate_suno_v6_payload
        from src.song_creator import create_complete_song_bundle

        parts = shlex.split(arg) if arg.strip() else []
        theme = "dark glam electropop"
        title = ""
        gender = "f"
        engine = "llm"
        mode = "3k"
        assets = False

        i = 0
        theme_parts = []
        while i < len(parts):
            p = parts[i]
            if p == "--title" and i + 1 < len(parts):
                title = parts[i + 1]
                i += 2
            elif p == "--gender" and i + 1 < len(parts):
                gender = parts[i + 1].lower()
                i += 2
            elif p == "--mode" and i + 1 < len(parts):
                mode = parts[i + 1].lower()
                i += 2
            elif p == "--engine" and i + 1 < len(parts):
                engine = parts[i + 1].lower()
                i += 2
            elif p == "--assets":
                assets = True
                i += 1
            else:
                theme_parts.append(p)
                i += 1
        if theme_parts:
            theme = " ".join(theme_parts)

        if assets or mode == "both":
            self.do_song(f'"{theme}" --title "{title or "New Name on the Door"}" --gender {gender}')
            return

        print(f"[*] Generating Suno Studio {mode.upper()} configuration ({engine} engine)...")
        payload = generate_suno_v6_payload(
            theme=theme,
            title=title,
            vocal_gender=gender,
            engine=engine,
            ref_model=self.model,
            mode=mode,
        )
        formatted_json = json.dumps(payload, indent=2, ensure_ascii=False)
        print("\n" + "=" * 60)
        print(f"  SUNO STUDIO V6 COMPATIBLE JSON PAYLOAD ({mode.upper()}: {len(formatted_json):,} chars)")
        print("=" * 60)
        print(formatted_json)
        print("=" * 60)

        slug = re.sub(r"[^a-z0-9]+", "_", (payload.get("title") or theme).lower()).strip("_")[:40]
        out_json = self.prompts_dir / f"v6_{slug}_{mode}.json"
        out_json.write_text(formatted_json, encoding="utf-8")
        print(f"[+] Saved V6 JSON ({len(formatted_json):,} chars) to: {out_json}\n")

    def do_song(self, arg: str) -> None:
        """Create a FULL NEW SONG bundle with 3k & 5k JSON payloads, LRC, brief, and cover prompt.
        Usage: song [theme] [--title "Song Title"] [--gender f|m] [--bpm 122]
        Example: song "cyberpunk bass rage" --title "Silicon Guillotine" --gender f
        """
        from src.song_creator import create_complete_song_bundle

        parts = shlex.split(arg) if arg.strip() else []
        theme = "dark glam electropop, cold radio pop"
        title = ""
        gender = ""
        bpm = 122
        lyrics = ""
        lyrics_file = None
        lipogram = ""
        engine = "llm"
        custom_text = ""
        ref_url = ""
        image_prompt = ""
        render_video = True

        i = 0
        theme_parts = []
        while i < len(parts):
            p = parts[i]
            if p in ("--title", "-t") and i + 1 < len(parts):
                title = parts[i + 1]
                i += 2
            elif p in ("--gender", "--vocal", "-v") and i + 1 < len(parts):
                gender = parts[i + 1].lower()
                i += 2
            elif p in ("--bpm", "-b") and i + 1 < len(parts):
                bpm = int(parts[i + 1])
                i += 2
            elif p in ("--text", "-tx") and i + 1 < len(parts):
                custom_text = parts[i + 1]
                i += 2
            elif p in ("--ref", "-r") and i + 1 < len(parts):
                ref_url = parts[i + 1]
                i += 2
            elif p in ("--image-prompt", "-ip") and i + 1 < len(parts):
                image_prompt = parts[i + 1]
                i += 2
            elif p in ("--no-video",):
                render_video = False
                i += 1
            elif p in ("--lyrics", "-l") and i + 1 < len(parts):
                lyrics = parts[i + 1]
                i += 2
            elif p in ("--lyrics-file", "-lf") and i + 1 < len(parts):
                lyrics_file = parts[i + 1]
                i += 2
            elif p in ("--lipogram",) and i + 1 < len(parts):
                lipogram = parts[i + 1]
                i += 2
            elif p in ("--engine",) and i + 1 < len(parts):
                engine = parts[i + 1].lower()
                i += 2
            else:
                theme_parts.append(p)
                i += 1
        if theme_parts:
            theme = " ".join(theme_parts)

        bundle = create_complete_song_bundle(
            title=title,
            theme=theme,
            vocal_gender=gender,
            bpm=bpm,
            custom_text=custom_text,
            reference_image_url=ref_url,
            image_prompt=image_prompt,
            render_video=render_video,
            out_dir=Path("output/songs"),
            lyrics=lyrics,
            lyrics_file=lyrics_file,
            lipogram=lipogram,
            engine=engine,
        )
        print("\n" + "=" * 65)
        print(f"  3K SUNO STUDIO V6 JSON PAYLOAD ({bundle['len_3k']:,} characters)")
        print("=" * 65)
        print(json.dumps(bundle["payload_3k"], indent=2, ensure_ascii=False))
        print("\n" + "=" * 65)
        print(f"  5K EXTENDED STUDIO V6 JSON PAYLOAD ({bundle['len_5k']:,} characters)")
        print("=" * 65)
        print(json.dumps(bundle["payload_5k"], indent=2, ensure_ascii=False))
        print("=" * 65)
        if bundle.get("cover_png"):
            print(f"  Cover Art (PNG): {bundle['cover_png']}")
        if bundle.get("teaser_video"):
            print(f"  Teaser Video:    {bundle['teaser_video']} (10s 1080p Ultra HD 60fps MP4)")
        print("=" * 65)

    def do_wizard(self, arg: str) -> None:
        """Launch the step-by-step guided wizard that holds your hand through full song creation."""
        from src.wizard import run_guided_wizard
        run_guided_wizard(out_dir=Path("output/songs"), engine="llm")

    def do_trending(self, arg: str) -> None:
        """Fetch live trending songs from Suno.com explore feed and optionally retrain model.
        Usage: trending [--train]
        """
        from src.downloader import SunoSongDownloader
        from src.trainer import train_from_trending

        if "--train" in arg or "train" in arg:
            train_from_trending(catalog_path=self.catalog_path, inference_path=self.inference_path)
            self.catalog = SongCatalogStore(self.catalog_path)
            self.model = SongwritingReferenceModel(self.inference_path)
            return

        dl = SunoSongDownloader()
        clips = dl.fetch_unified_feed(feed_id="trending", page_size=20, max_items=10)
        print("\n" + "=" * 65)
        print("  🔥 LIVE SUNO.COM TRENDING HITS")
        print("=" * 65)
        for idx, c in enumerate(clips[:10], start=1):
            title = str(c.get("title") or "Untitled")
            upvotes = c.get("upvote_count") or 0
            plays = c.get("play_count") or 0
            meta = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
            tags = str(meta.get("tags") or c.get("tags") or "Pop")
            print(f"[{idx}] {title}")
            print(f"    Tags:    {tags[:70]}")
            print(f"    Likes:   {upvotes:,} | Plays: {plays:,}")
            print(f"    Link:    https://suno.com/song/{c.get('id')}")
            print("-" * 65)
        print("\nTip: Type 'trending --train' to automatically ingest these tracks and retrain your local model!\n")

    def do_cover(self, arg: str) -> None:
        """Create custom 1024x1024 album cover art with custom typography overlay.
        Usage: cover "Song Title" [--genre kpop] [--text "Custom Text"] [--ref "http://..."]
        """
        parts = shlex.split(arg) if arg.strip() else []
        if not parts:
            print("Usage: cover \"Song Title\" [--genre kpop] [--text \"Custom Text\"] [--ref \"http://...\"]")
            return
        title = parts[0]
        genre = "pop"
        custom_text = ""
        ref_url = ""
        i = 1
        while i < len(parts):
            if parts[i] in ("--genre", "-g") and i + 1 < len(parts):
                genre = parts[i + 1]
                i += 2
            elif parts[i] in ("--text", "-t") and i + 1 < len(parts):
                custom_text = parts[i + 1]
                i += 2
            elif parts[i] in ("--ref", "-r") and i + 1 < len(parts):
                ref_url = parts[i + 1]
                i += 2
            else:
                i += 1
        from src.cover_studio import create_song_cover
        res = create_song_cover(title, genre=genre, custom_text=custom_text, reference_image_url=ref_url, out_dir=Path("output/covers"))
        print(f"[+] Cover PNG: {res['png_path']}")
        print(f"[+] Cover JPG: {res['jpg_path']}")

    def do_video(self, arg: str) -> None:
        """Render 10-second animated video teaser (1080x1080 MP4) from cover art.
        Usage: video <cover_png_path> [--title "Song Title"] [--bpm 128]
        """
        parts = shlex.split(arg) if arg.strip() else []
        if not parts:
            print("Usage: video <cover_png_path> [--title \"Song Title\"] [--bpm 128]")
            return
        cover_path = Path(parts[0])
        title = "Song Teaser"
        bpm = 122
        i = 1
        while i < len(parts):
            if parts[i] in ("--title", "-t") and i + 1 < len(parts):
                title = parts[i + 1]
                i += 2
            elif parts[i] in ("--bpm", "-b") and i + 1 < len(parts):
                bpm = int(parts[i + 1])
                i += 2
            else:
                i += 1
        from src.cover_studio import generate_10s_teaser_video
        out_vid = cover_path.parent / f"{cover_path.stem}_teaser_10s.mp4"
        vid = generate_10s_teaser_video(cover_path, out_vid, bpm=bpm, title=title)
        if vid:
            print(f"[+] 10-Second Teaser Video Created: {vid}")

    def do_gen(self, arg: str) -> None:
        """Alias for generate."""
        self.do_generate(arg)

    def do_generate(self, arg: str) -> None:
        """Generate a Suno Custom-mode ready prompt seed.
        Usage: generate [theme] [--tier viral|high|medium|low] [--title "Song Title"]
        Example: generate "midnight highway drive" --tier viral
        """
        parts = shlex.split(arg) if arg.strip() else []
        theme = "viral night drive"
        tier = "high"
        title = ""

        i = 0
        theme_parts = []
        while i < len(parts):
            p = parts[i]
            if p == "--tier" and i + 1 < len(parts):
                tier = parts[i + 1].lower()
                i += 2
            elif p == "--title" and i + 1 < len(parts):
                title = parts[i + 1]
                i += 2
            else:
                theme_parts.append(p)
                i += 1
        if theme_parts:
            theme = " ".join(theme_parts)

        seed = self.model.generate_prompt_seed(theme=theme, tier=tier, title=title)
        print("\n" + "=" * 60)
        print("  PASTE-READY SUNO PROMPT")
        print("=" * 60)
        print(seed.get("paste_ready"))
        print("=" * 60)

        # Save to prompts dir
        slug = re.sub(r"[^a-z0-9]+", "_", (title or theme).lower()).strip("_")[:40]
        out_txt = self.prompts_dir / f"prompt_{slug}.txt"
        out_json = self.prompts_dir / f"prompt_{slug}.json"
        out_txt.write_text(str(seed.get("paste_ready") or ""), encoding="utf-8")
        out_json.write_text(json.dumps(seed, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[+] Saved to: {out_txt}\n")

    def do_batch(self, arg: str) -> None:
        """Generate multiple prompts in batch.
        Usage: batch <count> [themes separated by comma]
        Example: batch 5 "love, money, heartbreak, high-speed highway, cyberpunk club"
        """
        parts = shlex.split(arg)
        if not parts:
            print("Usage: batch <count> [comma-separated themes]")
            return
        try:
            count = int(parts[0])
        except ValueError:
            print("Error: count must be a number.")
            return

        themes_arg = " ".join(parts[1:]) if len(parts) > 1 else ""
        themes = [t.strip() for t in themes_arg.split(",") if t.strip()]
        if not themes:
            themes = [
                "viral night drive",
                "stadium rock anthem",
                "late night bedroom confession",
                "cyberpunk bass rage",
                "acoustic campfire reflection",
            ]

        print(f"[*] Generating {count} song prompts in batch to {self.prompts_dir}...")
        for i in range(count):
            theme = themes[i % len(themes)]
            slug = re.sub(r"[^a-z0-9]+", "_", theme.lower())[:30].strip("_")
            path = self.prompts_dir / f"batch_{i+1:02d}_{slug}.txt"
            self.model.write_prompt_file(path, theme=theme, tier="high")
            print(f"  [+] Wrote: {path.name}")
        print("[+] Batch generation complete!\n")

    def do_suggest(self, arg: str) -> None:
        """Suggest trending style packs and unused novel style vocabulary."""
        print("\n--- POPULAR HIGH-TRACTION STYLES ---")
        pop = self.model.suggest_style_pack(tier="viral")
        print(f"Viral Style Pack:  {pop.style_pack}")
        high = self.model.suggest_style_pack(tier="high")
        print(f"High-Traction:     {high.style_pack}")

        print("\n--- UNUSED & NOVEL STYLE VOCABULARY ---")
        unused = self.model.suggest_unused_style_pack(self.catalog)
        print(f"Explore Pack:      {unused.style_pack}\n")

    def do_train(self, arg: str) -> None:
        """Retrain model from catalog, or ingest a new Suno song URL, profile, or created songs.
        Usage:
          train                      (retrains model from local catalog DB)
          train @wren                (fetches all songs from suno.com/@wren & retrains)
          train created              (ingests any created/handcrafted songs & retrains)
          train all                  (trains on @wren profile + created songs)
          train <suno_song_url>      (downloads audio, transcribes lyrics, and retrains)
        """
        target = arg.strip()
        from src.trainer import train_from_profile, train_from_created
        if target.startswith("@") or "suno.com/@" in target or target.lower() == "wren":
            print(f"[*] Ingesting and training from profile: {target}...")
            train_from_profile(target, catalog_path=self.catalog_path, inference_path=self.inference_path)
            self.catalog = SongCatalogStore(self.catalog_path)
            self.model = SongwritingReferenceModel(self.inference_path)
        elif target.lower() in ("created", "new"):
            print("[*] Ingesting handcrafted and created songs...")
            train_from_created(catalog_path=self.catalog_path, inference_path=self.inference_path)
            self.catalog = SongCatalogStore(self.catalog_path)
            self.model = SongwritingReferenceModel(self.inference_path)
        elif target.lower() in ("all", "full"):
            print("[*] Ingesting @wren profile + created songs...")
            train_from_profile("wren", catalog_path=self.catalog_path, inference_path=self.inference_path)
            train_from_created(catalog_path=self.catalog_path, inference_path=self.inference_path)
            self.catalog = SongCatalogStore(self.catalog_path)
            self.model = SongwritingReferenceModel(self.inference_path)
        elif target.startswith("http") or re.search(r"[0-9a-f]{8}-[0-9a-f]{4}", target):
            print(f"[*] Ingesting and training from URL: {target}...")
            train_from_url(
                target,
                catalog_path=self.catalog_path,
                inference_path=self.inference_path,
            )
            # Reload updated model
            self.catalog = SongCatalogStore(self.catalog_path)
            self.model = SongwritingReferenceModel(self.inference_path)
        else:
            print("[*] Retraining SongwritingReferenceModel from local catalog...")
            n = self.model.train_from_catalog(self.catalog)
            self.model.save()
            print(f"[+] Retrained on {n} songs in {self.catalog_path}")
            print(self.model.format_report())

    def do_similar(self, arg: str) -> None:
        """Find catalog songs with similar style and signature.
        Usage: similar <song_uuid>
        """
        sid = arg.strip()
        if not sid:
            print("Usage: similar <song_id_uuid>")
            return
        rec = self.catalog.get(sid)
        if not rec:
            print(f"Song not found in catalog: {sid}")
            return
        results = self.model.discover_similar(rec, self.catalog, limit=6)
        print(f"\nSongs similar to '{rec.title}' ({rec.derived_style_signature[:50]}...):")
        for s in results:
            print(f"  Score: {s.score:.3f} | {s.like_count} likes | {s.title[:45]} | {s.url}")
        print()

    def parseline(self, line: str):
        line = line.lstrip("\ufeff\xef\xbb\xbf \t\r\n")
        if line.startswith("ï»¿"):
            line = line[3:]
        # Automatically strip accidentally pasted prompt prefixes (e.g. 'suno> song ...', 'suno> suno> song ...')
        line = re.sub(r"^(suno\s*>|suno:|suno\b|>|\s)+\s*", "", line, flags=re.I).strip()
        return super().parseline(line)

    def precmd(self, line: str) -> str:
        line = line.lstrip("\ufeff\xef\xbb\xbf \t\r\n")
        if line.startswith("ï»¿"):
            line = line[3:]
        cleaned = re.sub(r"^(suno\s*>|suno:|suno\b|>|\s)+\s*", "", line, flags=re.I).strip()
        if cleaned:
            self.cmd_history.append(cleaned)
        return cleaned

    def default(self, line: str) -> None:
        clean = re.sub(r"^(suno\s*>|suno:|suno\b|>|\s)+\s*", "", line, flags=re.I).strip()
        if clean and clean != line.strip():
            self.onecmd(clean)
            return
        super().default(line)

    def postloop(self) -> None:
        if readline:
            try:
                readline.write_history_file(str(self.history_file))
            except Exception:
                pass

    def do_history(self, arg: str) -> None:
        """Display recent command history or clear it.
        Usage:
          history            (view command history)
          history clear      (clear command history)
          history -c         (clear command history)
        """
        sub = arg.strip().lower()
        if sub in ("clear", "-c", "--clear"):
            self.do_clear_history("")
            return
        if not self.cmd_history:
            print("No command history yet.")
            return
        print("\n--- REPL COMMAND HISTORY ---")
        for idx, cmd_str in enumerate(self.cmd_history, 1):
            print(f"  {idx:3d}: {cmd_str}")
        print("----------------------------\n")

    def do_clear_history(self, arg: str) -> None:
        """Clear the command line history buffer and history file.
        Usage: clear_history
        """
        self.cmd_history.clear()
        if readline:
            try:
                readline.clear_history()
            except Exception:
                pass
        if self.history_file.exists():
            try:
                self.history_file.unlink()
            except Exception:
                pass
        print("[+] REPL command history cleared.")

    def do_clear(self, arg: str) -> None:
        """Clear the terminal screen or clear command history.
        Usage:
          clear              (clears the screen)
          clear history      (clears command history)
          clear all          (clears both screen and command history)
        """
        sub = arg.strip().lower()
        import os
        if sub in ("history", "-h"):
            self.do_clear_history("")
        elif sub == "all":
            self.do_clear_history("")
            os.system("cls" if os.name == "nt" else "clear")
        else:
            os.system("cls" if os.name == "nt" else "clear")

    def do_listen(self, arg: str) -> None:
        """Download and transcribe lyrics from a Suno song URL.
        Usage: listen <suno_song_url>
        Example: listen https://suno.com/song/8ac118c0-3aab-43ac-af8f-57dbd1368e29
        """
        target = arg.strip()
        if not target:
            print("Usage: listen <suno_song_url>")
            return
        from src.downloader import SunoSongDownloader
        from src.transcriber import SunoAudioTranscriber

        dl = SunoSongDownloader(output_dir="output/audio")
        song = dl.fetch_song(target, download_audio=True)
        if song.downloaded_audio_path:
            tr = SunoAudioTranscriber(transcripts_dir="output/transcripts")
            res = tr.transcribe(song.downloaded_audio_path, song_id=song.song_id)
            print("\n--- TRANSCRIBED LYRICS ---\n")
            print(res["lyrics"])
            print("--------------------------\n")

    def do_deploy(self, arg: str) -> None:
        """Deploy this system live to Hugging Face Spaces.
        Usage: deploy [repo_id]
        """
        from src.deploy import deploy_to_hf_space

        target = arg.strip() or "suno-song-generator"
        try:
            deploy_to_hf_space(target)
        except Exception as e:
            print(f"[!] Deployment error: {e}")

    def do_quit(self, arg: str) -> bool:
        """Exit the Suno REPL harness."""
        print("Goodbye!")
        return True

    def do_exit(self, arg: str) -> bool:
        """Exit the Suno REPL harness."""
        return self.do_quit(arg)

    def help_gen(self) -> None:
        self.help_generate()

    def help_generate(self) -> None:
        print("\nGenerate a Suno Custom-mode ready prompt seed.")
        print("Usage: generate [theme] [--tier viral|high|medium|low] [--title \"Song Title\"]")
        print("Example: generate \"midnight neon drive\" --tier viral --title \"Night Racer\"\n")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Suno REPL Harness")
    parser.add_argument("--catalog", default="models/suno_song_catalog.json")
    parser.add_argument("--inference", default="models/suno_song_inference_model.json")
    parser.add_argument("--prompts-dir", default="output/prompts")
    args = parser.parse_args()

    # If running from inside dist/, adjust default paths
    cat = Path(args.catalog)
    inf = Path(args.inference)
    if not cat.exists() and Path("dist/models/suno_song_catalog.json").exists():
        cat = Path("dist/models/suno_song_catalog.json")
    if not inf.exists() and Path("dist/models/suno_song_inference_model.json").exists():
        inf = Path("dist/models/suno_song_inference_model.json")

    app = SunoReplHarness(catalog_path=cat, inference_path=inf, prompts_dir=args.prompts_dir)
    try:
        app.cmdloop()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
