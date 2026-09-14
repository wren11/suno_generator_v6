"""Suno AI Live Trending Monitor & Auto-Trainer.

Continuously monitors https://suno.com/explore/feed/trending and Suno Explore feeds
for new songs that have not yet been trained, downloads the audio, transcribes lyrics
with Whisper, updates the catalog, and retrains the statistical inference model.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.catalog import SongCatalogStore, resolve_catalog_path
from src.inference import resolve_inference_path
from src.trainer import train_from_url

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_DEFAULT_FEED_URL = "https://suno.com/explore/feed/trending"
_EXPLORE_PLAYLIST_URL = "https://studio-api.prod.suno.com/api/playlist/1190bf92-10dc-4ce5-968a-7a377f37f984/?page=1"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class AutoTrainTracker:
    """Maintains a persistent registry of all songs already processed and trained."""

    def __init__(
        self,
        state_path: str | Path = "dist/models/auto_train_processed.json",
        catalog_path: str | Path = "dist/models/suno_song_catalog.json",
    ) -> None:
        self.state_path = Path(state_path)
        self.catalog_path = Path(catalog_path)
        self.processed_ids: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load previously processed IDs from state file and catalog store."""
        # Step 1: Pre-populate from existing catalog (so all existing songs are marked processed)
        cat_file = resolve_catalog_path(self.catalog_path)
        if cat_file.exists():
            try:
                store = SongCatalogStore(cat_file)
                for sid in store.all_ids():
                    clean_id = sid.lower().strip()
                    if clean_id not in self.processed_ids:
                        rec = store.get(clean_id)
                        self.processed_ids[clean_id] = {
                            "title": rec.title if rec else "Catalog Track",
                            "artist": rec.artist_name if rec else "",
                            "url": f"https://suno.com/song/{clean_id}",
                            "processed_at": "catalog_existing",
                            "status": "in_catalog",
                        }
            except Exception as e:
                print(f"[!] Warning reading catalog for processed IDs: {e}")

        # Step 2: Load state file if exists
        state_file = self.state_path
        if not state_file.exists() and Path("models/auto_train_processed.json").exists():
            state_file = Path("models/auto_train_processed.json")

        if state_file.exists():
            try:
                with open(state_file, encoding="utf-8") as f:
                    data = json.loads(f.read())
                    file_processed = data.get("processed_ids") or {}
                    for sid, info in file_processed.items():
                        self.processed_ids[sid.lower().strip()] = info
            except Exception as e:
                print(f"[!] Warning reading state file: {e}")

    def is_processed(self, song_id: str) -> bool:
        return song_id.lower().strip() in self.processed_ids

    def mark_processed(
        self,
        song_id: str,
        title: str = "",
        artist: str = "",
        url: str = "",
        status: str = "trained",
    ) -> None:
        cid = song_id.lower().strip()
        self.processed_ids[cid] = {
            "title": title,
            "artist": artist,
            "url": url or f"https://suno.com/song/{cid}",
            "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "status": status,
        }
        self.save()

    def save(self) -> None:
        """Persist state file to disk and mirror to models/ directory if present."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            "total_processed": len(self.processed_ids),
            "processed_ids": self.processed_ids,
        }
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        # Mirror to models/ if models folder exists and differs
        root_state = Path("models/auto_train_processed.json")
        if root_state.parent.exists() and root_state != self.state_path:
            try:
                root_state.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass


class SunoTrendingMonitor:
    """Discovers and scrapes songs currently featured on Suno explore and trending feeds."""

    def __init__(self, user_agent: str = _USER_AGENT) -> None:
        self.user_agent = user_agent

    def fetch_trending_songs(self, feed_url: str = _DEFAULT_FEED_URL) -> list[dict[str, Any]]:
        """
        Fetch all songs currently on the trending feed using a robust multi-source strategy:
        1. Suno Live Explore / Trending Playlist API (Top 48 hits directly with metadata & stream URLs)
        2. Web scraper on the target feed URL (https://suno.com/explore/feed/trending)
        3. Web scraper on fallback feed (https://suno.com/feed/trending)
        """
        songs: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        # Strategy 1: Suno Explore / Trending Top Songs Playlist
        try:
            req = urllib.request.Request(_EXPLORE_PLAYLIST_URL, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=12) as resp:
                pdata = json.loads(resp.read().decode("utf-8"))
                clips = pdata.get("playlist_clips") or []
                for item in clips:
                    c = item.get("clip") or {}
                    cid = str(c.get("id") or "").lower().strip()
                    if cid and cid not in seen_ids:
                        seen_ids.add(cid)
                        songs.append({
                            "id": cid,
                            "url": f"https://suno.com/song/{cid}",
                            "title": c.get("title") or "Untitled Track",
                            "artist": c.get("display_name") or c.get("handle") or "Unknown",
                            "handle": c.get("handle") or "",
                            "tags": c.get("metadata", {}).get("tags") or "",
                            "play_count": c.get("play_count") or 0,
                            "like_count": c.get("upvote_count") or 0,
                            "source": "explore_playlist",
                        })
        except Exception as ex:
            print(f"[!] Warning: Explore playlist API check encountered: {ex}")

        # Strategy 2: Direct scrape of target feed URL
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(
                    r"/song/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
                    html,
                )
                for m in matches:
                    cid = m.lower().strip()
                    if cid and cid not in seen_ids:
                        seen_ids.add(cid)
                        songs.append({
                            "id": cid,
                            "url": f"https://suno.com/song/{cid}",
                            "title": "Suno Trending Track",
                            "artist": "Trending Artist",
                            "handle": "",
                            "tags": "",
                            "play_count": 0,
                            "like_count": 0,
                            "source": "feed_url_scrape",
                        })
        except Exception as ex:
            print(f"[!] Warning: Feed URL scrape ({feed_url}) encountered: {ex}")

        return songs


class SunoAutoTrainer:
    """Main daemon that continuously polls Suno trending feeds and auto-trains new tracks."""

    def __init__(
        self,
        recheck_interval: int = 30,
        feed_url: str = _DEFAULT_FEED_URL,
        catalog_path: str | Path = "dist/models/suno_song_catalog.json",
        inference_path: str | Path = "dist/models/suno_song_inference_model.json",
        audio_dir: str | Path = "dist/output/audio",
        transcripts_dir: str | Path = "dist/output/transcripts",
        whisper_model: str = "base",
        hf_token: str | None = None,
        max_songs_per_check: int = 0,
    ) -> None:
        self.recheck_interval = max(int(recheck_interval), 1)
        self.feed_url = feed_url
        self.catalog_path = resolve_catalog_path(catalog_path)
        self.inference_path = resolve_inference_path(inference_path)
        self.audio_dir = Path(audio_dir)
        self.transcripts_dir = Path(transcripts_dir)
        self.whisper_model = whisper_model
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.max_songs_per_check = max_songs_per_check

        self.tracker = AutoTrainTracker(
            state_path="dist/models/auto_train_processed.json",
            catalog_path=self.catalog_path,
        )
        self.monitor = SunoTrendingMonitor()

    def run_sweep(self) -> int:
        """Run a single detection and training sweep. Returns count of newly trained songs."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[*] [{now_str}] Checking Suno Trending Feed: {self.feed_url} ...")

        trending_candidates = self.monitor.fetch_trending_songs(self.feed_url)
        if not trending_candidates:
            print("[!] Could not retrieve any songs from trending feeds. Will retry on next cycle.")
            return 0

        # Filter against already processed songs
        new_songs = [s for s in trending_candidates if not self.tracker.is_processed(s["id"])]
        already_processed = len(trending_candidates) - len(new_songs)

        print(
            f"[+] Feed scan complete: {len(trending_candidates)} trending songs checked "
            f"({len(new_songs)} new, {already_processed} already processed)."
        )

        if not new_songs:
            print(f"[i] All songs on the trending feed are already processed and in the model.")
            return 0

        if self.max_songs_per_check > 0:
            new_songs = new_songs[: self.max_songs_per_check]

        print("=" * 65)
        print(f"  🔥 DETECTED {len(new_songs)} NEW TRENDING SONG(S) TO TRAIN!")
        print("=" * 65)
        for idx, s in enumerate(new_songs, 1):
            print(f"  [{idx}/{len(new_songs)}] {s['title']} ({s['id']}) by {s['artist']}")
            print(f"       URL: {s['url']}")
        print("-" * 65)

        trained_count = 0
        for idx, song in enumerate(new_songs, 1):
            print(f"\n>>> [{idx}/{len(new_songs)}] INGESTING & RETRAINING: \"{song['title']}\" ...")
            try:
                res = train_from_url(
                    song["url"],
                    catalog_path=self.catalog_path,
                    inference_path=self.inference_path,
                    audio_dir=self.audio_dir,
                    transcripts_dir=self.transcripts_dir,
                    hf_token=self.hf_token,
                    whisper_model=self.whisper_model,
                )
                self.tracker.mark_processed(
                    song_id=song["id"],
                    title=song["title"],
                    artist=song["artist"],
                    url=song["url"],
                    status="trained",
                )
                trained_count += 1
                print(f"[+] Successfully trained track #{idx}: {song['title']}")
            except Exception as ex:
                print(f"[!] Error training song {song['id']}: {ex}")
                # Mark as attempted with error
                self.tracker.mark_processed(
                    song_id=song["id"],
                    title=song["title"],
                    artist=song["artist"],
                    url=song["url"],
                    status=f"error: {ex}",
                )

        print("=" * 65)
        print(f"[+] Auto-training sweep finished: {trained_count} new song(s) added to model.")
        print(f"    Total songs in catalog: {len(self.tracker.processed_ids)}")
        print("=" * 65)
        return trained_count

    def run_daemon(self) -> None:
        """Run continuous monitoring loop with configurable recheck interval."""
        print("=" * 70)
        print("  ____  _   _ _   _  ___     _   _   _ _____ ___   _____ ____     _    ___ _   _ ")
        print(" / ___|| | | | \ | |/ _ \   / \ | | | |_   _/ _ \ |_   _|  _ \   / \  |_ _| \ | |")
        print(" \___ \| | | |  \| | | | | / _ \| | | | | || | | |  | | | |_) | / _ \  | ||  \| |")
        print("  ___) | |_| | |\  | |_| |/ ___ \ |_| | | || |_| |  | | |  _ < / ___ \ | || |\  |")
        print(" |____/ \___/|_| \_|\___//_/   \_\___/  |_| \___/   |_| |_| \_/_/   \_\___|_| \_|")
        print("                                                                                  ")
        print("  Suno AI Live Trending Monitor & Automated Retraining Engine v1.0")
        print("======================================================================")
        print(f"Target Feed:        {self.feed_url}")
        print(f"Recheck Interval:   {self.recheck_interval} seconds")
        print(f"Catalog Database:   {self.catalog_path}")
        print(f"Inference Model:    {self.inference_path}")
        print(f"Whisper Model:      {self.whisper_model}")
        print(f"Processed Registry: {len(self.tracker.processed_ids)} tracks currently tracked")
        print("======================================================================")
        print("  Press Ctrl+C at any time to gracefully pause or stop.")
        print("======================================================================\n")

        try:
            while True:
                self.run_sweep()
                self._sleep_countdown(self.recheck_interval)
        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("  [!] Auto-Trainer stopped by user (Ctrl+C).")
            print(f"  [+] Total tracked songs in state: {len(self.tracker.processed_ids)}")
            print("======================================================================\n")

    def _sleep_countdown(self, seconds: int) -> None:
        """Sleep with responsive interrupt check and clean terminal countdown."""
        sys.stdout.write(f"[i] Sleeping {seconds}s before next recheck (Press Ctrl+C to stop)...")
        sys.stdout.flush()
        for remaining in range(seconds, 0, -1):
            time.sleep(1)
            # Update countdown every 5 seconds or when under 5 seconds
            if remaining <= 5 or remaining % 10 == 0:
                sys.stdout.write(f"\r[i] Sleeping {remaining}s before next recheck (Press Ctrl+C to stop)...   ")
                sys.stdout.flush()
        sys.stdout.write("\r" + " " * 75 + "\r")
        sys.stdout.flush()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suno AI Live Trending Monitor & Auto-Trainer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--recheck",
        "-r",
        type=int,
        default=30,
        help="Seconds before rechecking the Suno trending feed (default: 30)",
    )
    parser.add_argument(
        "--feed-url",
        "-f",
        type=str,
        default=_DEFAULT_FEED_URL,
        help="Suno feed URL to monitor",
    )
    parser.add_argument(
        "--catalog",
        "-c",
        type=str,
        default="dist/models/suno_song_catalog.json",
        help="Path to song catalog JSON",
    )
    parser.add_argument(
        "--inference",
        "-i",
        type=str,
        default="dist/models/suno_song_inference_model.json",
        help="Path to inference model JSON",
    )
    parser.add_argument(
        "--audio-dir",
        type=str,
        default="dist/output/audio",
        help="Directory to save downloaded audio streams",
    )
    parser.add_argument(
        "--transcripts-dir",
        type=str,
        default="dist/output/transcripts",
        help="Directory to save transcribed lyrics",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default="base",
        help="Whisper model size (tiny, base, small, medium, large-v3)",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Optional Hugging Face token for Whisper Inference API",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single sweep of the trending feed and exit",
    )
    parser.add_argument(
        "--max-songs",
        type=int,
        default=0,
        help="Maximum new songs to train per check cycle (0 = unlimited)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    trainer = SunoAutoTrainer(
        recheck_interval=args.recheck,
        feed_url=args.feed_url,
        catalog_path=args.catalog,
        inference_path=args.inference,
        audio_dir=args.audio_dir,
        transcripts_dir=args.transcripts_dir,
        whisper_model=args.whisper_model,
        hf_token=args.hf_token,
        max_songs_per_check=args.max_songs,
    )

    if args.once:
        count = trainer.run_sweep()
        print(f"\n[+] Single sweep complete. Newly trained tracks: {count}")
        return 0

    trainer.run_daemon()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
