"""Suno AI Live Target Monitor & Auto-Trainer.

Continuously monitors Suno targets:
  1. User Profiles (e.g. @wren, https://suno.com/@wren, https://suno.com/profile/wren)
  2. Playlists (e.g. https://suno.com/playlist/<uuid>, bare playlist UUIDs)
  3. Single Songs (e.g. https://suno.com/song/<uuid>)
  4. Trending / Explore Feeds (https://suno.com/explore/feed/trending)

Automatically detects new songs not yet trained, downloads progressive audio,
transcribes lyrics with Whisper, indexes musical tags and Markov chains, and
retrains the statistical songwriting reference model.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.parse
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


def detect_target_type(target: str) -> tuple[str, str]:
    """Detect whether target is a profile, playlist, single song, or trending feed.

    Returns:
        (target_type, normalized_value)
        target_type can be: 'profile', 'playlist', 'song', 'feed'
    """
    t = (target or "").strip()
    if not t:
        return ("feed", _DEFAULT_FEED_URL)

    # 1. Profile with @ prefix (e.g. @wren)
    if t.startswith("@"):
        return ("profile", t.lstrip("@").strip())

    # 2. Profile URL (e.g. https://suno.com/@wren or https://suno.com/profile/wren)
    m_prof = re.search(r"suno\.com/@([a-zA-Z0-9_\-]+)", t)
    if m_prof:
        return ("profile", m_prof.group(1).strip())
    m_prof2 = re.search(r"suno\.com/profile/([a-zA-Z0-9_\-]+)", t)
    if m_prof2:
        return ("profile", m_prof2.group(1).strip())

    # 3. Playlist URL (e.g. https://suno.com/playlist/<uuid> or studio-api.../playlist/<uuid>)
    if "playlist" in t:
        m_uuid = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", t)
        if m_uuid:
            return ("playlist", m_uuid.group(1).lower())

    # 4. Single song URL
    m_song = re.search(r"suno\.com/song/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", t)
    if m_song:
        return ("song", m_song.group(1).lower())

    # 5. Bare UUID (defaults to playlist / collection)
    if re.match(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", t):
        return ("playlist", t.lower())

    # 6. Suno or HTTP URL -> feed
    if t.startswith("http://") or t.startswith("https://"):
        return ("feed", t)

    # 7. Bare handle without @ (alphanumeric with underscores/hyphens)
    if re.match(r"^[a-zA-Z0-9_\-]+$", t):
        return ("profile", t)

    return ("feed", t)


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
                for rec in store.all_records():
                    clean_id = rec.song_id.lower().strip()
                    if clean_id not in self.processed_ids:
                        self.processed_ids[clean_id] = {
                            "title": rec.title or "Catalog Track",
                            "artist": rec.artist_name or "",
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

        root_state = Path("models/auto_train_processed.json")
        if root_state.parent.exists() and root_state.resolve() != self.state_path.resolve():
            try:
                root_state.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass


class SunoTargetMonitor:
    """Discovers and scrapes songs from Suno profiles, playlists, songs, or trending feeds."""

    def __init__(self, user_agent: str = _USER_AGENT) -> None:
        self.user_agent = user_agent

    def fetch_songs(self, target: str) -> tuple[str, str, list[dict[str, Any]]]:
        """Detect target type and retrieve all candidate songs.

        Returns:
            (target_type, display_description, list_of_song_dicts)
        """
        target_type, target_val = detect_target_type(target)

        if target_type == "profile":
            songs = self.fetch_profile_songs(target_val)
            return ("profile", f"User Profile @{target_val} (https://suno.com/@{target_val})", songs)

        elif target_type == "playlist":
            songs = self.fetch_playlist_songs(target_val)
            return ("playlist", f"Playlist {target_val} (https://suno.com/playlist/{target_val})", songs)

        elif target_type == "song":
            song = {
                "id": target_val,
                "url": f"https://suno.com/song/{target_val}",
                "title": f"Song {target_val}",
                "artist": "Suno Track",
                "handle": "",
                "tags": "",
                "play_count": 0,
                "like_count": 0,
                "source": "direct_song",
            }
            return ("song", f"Song {target_val} (https://suno.com/song/{target_val})", [song])

        else:  # feed
            songs = self.fetch_trending_songs(target_val)
            return ("feed", f"Trending Feed ({target_val})", songs)

    def fetch_profile_songs(self, handle: str, max_pages: int = 50) -> list[dict[str, Any]]:
        """Fetch all public songs from a Suno user profile across all paginated pages."""
        clean_handle = handle.strip().lstrip("@")
        if not clean_handle:
            return []

        songs: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        page = 1

        print(f"[*] Scanning Suno profile for @{clean_handle} ...")
        while page <= max_pages:
            url = (
                f"https://studio-api.prod.suno.com/api/profiles/{urllib.parse.quote(clean_handle)}"
                f"?playlists_sort_by=created_at&clips_sort_by=created_at&page={page}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            try:
                with urllib.request.urlopen(req, timeout=18) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print(f"[!] Error fetching profile @{clean_handle} page {page}: {e}")
                break

            clips = data.get("clips") or []
            if not clips:
                break

            new_in_page = 0
            for c in clips:
                cid = str(c.get("id") or "").lower().strip()
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    songs.append({
                        "id": cid,
                        "url": f"https://suno.com/song/{cid}",
                        "title": c.get("title") or "Untitled Track",
                        "artist": c.get("display_name") or c.get("handle") or f"@{clean_handle}",
                        "handle": c.get("handle") or clean_handle,
                        "tags": c.get("metadata", {}).get("tags") or "",
                        "play_count": c.get("play_count") or 0,
                        "like_count": c.get("upvote_count") or 0,
                        "source": f"profile_@{clean_handle}",
                    })
                    new_in_page += 1

            if new_in_page == 0 or len(clips) < 4:
                break
            page += 1
            time.sleep(0.2)

        return songs

    def fetch_playlist_songs(self, playlist_id: str, max_pages: int = 30) -> list[dict[str, Any]]:
        """Fetch all songs in a Suno playlist across all paginated pages."""
        clean_id = playlist_id.strip().lower()
        songs: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        page = 1

        print(f"[*] Scanning Suno playlist: {clean_id} ...")
        while page <= max_pages:
            url = f"https://studio-api.prod.suno.com/api/playlist/{clean_id}/?page={page}"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            try:
                with urllib.request.urlopen(req, timeout=18) as resp:
                    pdata = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print(f"[!] Error fetching playlist {clean_id} page {page}: {e}")
                break

            items = pdata.get("playlist_clips") or []
            if not items:
                break

            new_in_page = 0
            for item in items:
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
                        "source": f"playlist_{clean_id}",
                    })
                    new_in_page += 1

            if new_in_page == 0:
                break
            page += 1
            time.sleep(0.2)

        return songs

    def fetch_trending_songs(self, feed_url: str = _DEFAULT_FEED_URL) -> list[dict[str, Any]]:
        """Fetch trending hits via Explore Playlist API and HTML regex scraping."""
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


# Backwards compatibility alias
SunoTrendingMonitor = SunoTargetMonitor


class SunoAutoTrainer:
    """Main engine that polls Suno targets (profile, playlist, feed) and auto-trains new tracks."""

    def __init__(
        self,
        target: str = _DEFAULT_FEED_URL,
        recheck_interval: int = 30,
        catalog_path: str | Path = "dist/models/suno_song_catalog.json",
        inference_path: str | Path = "dist/models/suno_song_inference_model.json",
        audio_dir: str | Path = "dist/output/audio",
        transcripts_dir: str | Path = "dist/output/transcripts",
        whisper_model: str = "base",
        hf_token: str | None = None,
        max_songs_per_check: int = 0,
    ) -> None:
        self.target = target or _DEFAULT_FEED_URL
        self.recheck_interval = max(int(recheck_interval), 1)
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
        self.monitor = SunoTargetMonitor()

    def run_sweep(self) -> int:
        """Run a single detection and training sweep on the target. Returns count of newly trained songs."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_type, target_desc, candidates = self.monitor.fetch_songs(self.target)
        print(f"\n[*] [{now_str}] Polling [{target_type.upper()}]: {target_desc} ...")

        if not candidates:
            print(f"[!] Could not retrieve any songs from {target_desc}. Will retry on next cycle.")
            return 0

        # Filter against already processed songs
        new_songs = [s for s in candidates if not self.tracker.is_processed(s["id"])]
        already_processed = len(candidates) - len(new_songs)

        print(
            f"[+] Target scan complete: {len(candidates)} song(s) found "
            f"({len(new_songs)} new to train, {already_processed} already processed in catalog/registry)."
        )

        if not new_songs:
            print(f"[i] All songs from this target are already trained and in the model.")
            return 0

        if self.max_songs_per_check > 0:
            new_songs = new_songs[: self.max_songs_per_check]

        print("=" * 65)
        print(f"  🔥 DETECTED {len(new_songs)} NEW SONG(S) TO TRAIN!")
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
        target_type, target_desc = detect_target_type(self.target)

        print("=" * 70)
        print("  ____  _   _ _   _  ___     _   _   _ _____ ___   _____ ____     _    ___ _   _ ")
        print(" / ___|| | | | \ | |/ _ \   / \ | | | |_   _/ _ \ |_   _|  _ \   / \  |_ _| \ | |")
        print(" \___ \| | | |  \| | | | | / _ \| | | | | || | | |  | | | |_) | / _ \  | ||  \| |")
        print("  ___) | |_| | |\  | |_| |/ ___ \ |_| | | || |_| |  | | |  _ < / ___ \ | || |\  |")
        print(" |____/ \___/|_| \_|\___//_/   \_\___/  |_| \___/   |_| |_| \_/_/   \_\___|_| \_|")
        print("                                                                                  ")
        print("  Suno AI Live Target Monitor & Automated Retraining Engine v2.0")
        print("======================================================================")
        print()
        print(f"Monitoring Target:  [{target_type.upper()}] {self.target}")
        print(f"Recheck Interval:   {self.recheck_interval} seconds")
        print(f"Catalog Database:   {self.catalog_path}")
        print(f"Inference Model:    {self.inference_path}")
        print(f"Whisper Model:      {self.whisper_model}")
        print(f"Processed Registry: {len(self.tracker.processed_ids)} tracks currently tracked")
        print("======================================================================")
        print("  Press Ctrl+C at any time to gracefully pause or stop.")
        print("======================================================================")
        print()

        try:
            while True:
                self.run_sweep()
                self._sleep_countdown(self.recheck_interval)
        except KeyboardInterrupt:
            print()
            print("=" * 70)
            print("  [!] Auto-Trainer stopped by user (Ctrl+C).")
            print(f"  [+] Total tracked songs in state: {len(self.tracker.processed_ids)}")
            print("======================================================================")
            print()

    def _sleep_countdown(self, seconds: int) -> None:
        """Sleep with responsive interrupt check and clean terminal countdown."""
        sys.stdout.write(f"[i] Sleeping {seconds}s before next check (Press Ctrl+C to stop)...")
        sys.stdout.flush()
        for remaining in range(seconds, 0, -1):
            time.sleep(1)
            if remaining <= 5 or remaining % 10 == 0:
                sys.stdout.write(f"\r[i] Sleeping {remaining}s before next check (Press Ctrl+C to stop)...   ")
                sys.stdout.flush()
        sys.stdout.write("\r" + " " * 75 + "\r")
        sys.stdout.flush()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suno AI Live Target Monitor & Auto-Trainer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Monitoring target: profile (@wren, suno.com/@wren), playlist URL, song URL, or trending feed URL (default: trending feed)",
    )
    parser.add_argument(
        "--target",
        "-t",
        dest="target_flag",
        default=None,
        help="Explicit target flag (@username, playlist URL, song URL, or feed URL)",
    )
    parser.add_argument(
        "--recheck",
        "-r",
        type=int,
        default=30,
        help="Seconds before rechecking target for new songs (default: 30)",
    )
    parser.add_argument(
        "--feed-url",
        "-f",
        type=str,
        default=None,
        help="Legacy alias for --target / trending feed URL",
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
        help="Run a single sweep of the target and exit",
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

    # Smart detection: if positional target is purely digits, treat it as recheck interval
    target = args.target_flag or args.target or args.feed_url or _DEFAULT_FEED_URL
    recheck = args.recheck
    if args.target and args.target.isdigit() and not args.target_flag:
        recheck = int(args.target)
        target = args.feed_url or _DEFAULT_FEED_URL

    trainer = SunoAutoTrainer(
        target=target,
        recheck_interval=recheck,
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
