"""High-throughput Suno Trending & Explore Harvester.

Fetches brand new trending, explore, and top creator tracks from Suno's live APIs,
extracts complete lyrics and musical metadata, and ingests them directly into the
song catalog and auto-train registry until the target quota (default: 2,000 songs) is reached.
"""

from __future__ import annotations

import argparse
import collections
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

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Seed list of known high-traction creators and playlists across genres
INITIAL_HANDLES = [
    "wren", "rushyrush15", "rustyspork", "jackempire", "pepek39501",
    "gamelendez43", "darkangel198524", "aranyaauthaphan", "chaulong71",
    "maxvern24", "udgold", "mmepnoir", "e8784238", "chorivstrom",
    "hockeyalex31", "daleandmike", "fnaf_fart", "egorpradilsikov15",
    "justinmcdermitt", "osmaschz_1862", "rain_man_savitar", "nemesisheresy",
    "ollibean", "amlomc9480", "gracex1", "speakonlinesongs", "showafunk",
    "pradilsikovegor50706", "hotsauceoriginal136", "getnoodlebox",
    "curator", "explore", "suno", "trending", "ai_artist", "top_tracks",
    "beats", "synthwave", "retrowave", "hiphop", "popstar", "rocker",
    "metalhead", "chillhop", "lofi", "futurebass", "melodic", "countryboy"
]

INITIAL_PLAYLISTS = [
    "1190bf92-10dc-4ce5-968a-7a377f37f984",  # Explore playlist
]


class SunoHarvester:
    """Discovers and ingests new songs into the persistent song catalog."""

    def __init__(
        self,
        catalog_path: str | Path = "models/suno_song_catalog.json",
        tracker_path: str | Path = "models/auto_train_processed.json",
    ) -> None:
        self.catalog_path = Path(catalog_path)
        self.tracker_path = Path(tracker_path)
        self.catalog = SongCatalogStore(self.catalog_path)
        
        # Build set of already existing song UUIDs
        self.seen_ids: set[str] = set()
        for rec in self.catalog.all_records():
            self.seen_ids.add(rec.song_id.lower().strip())

        # Load tracker
        self.processed_ids: dict[str, dict[str, Any]] = {}
        if self.tracker_path.exists():
            try:
                with open(self.tracker_path, encoding="utf-8") as f:
                    tdata = json.load(f)
                    self.processed_ids = tdata.get("processed_ids", {})
                    for sid in self.processed_ids:
                        self.seen_ids.add(sid.lower().strip())
            except Exception as ex:
                print(f"[!] Warning reading tracker: {ex}")

        # Queues for graph traversal
        self.handle_queue: collections.deque[str] = collections.deque()
        self.visited_handles: set[str] = set()
        self.playlist_queue: collections.deque[str] = collections.deque()
        self.visited_playlists: set[str] = set()

        # Seed handles from existing catalog
        for rec in self.catalog.all_records():
            h = (rec.artist_id or "").strip().lstrip("@")
            if h and len(h) >= 3 and h not in self.visited_handles:
                self.handle_queue.append(h)

        for h in INITIAL_HANDLES:
            if h not in self.handle_queue:
                self.handle_queue.append(h)

        for p in INITIAL_PLAYLISTS:
            self.playlist_queue.append(p)

    def harvest(self, target_count: int = 2000) -> int:
        print("=" * 65)
        print("  SUNO HIGH-THROUGHPUT TRENDING & EXPLORE HARVESTER")
        print("=" * 65)
        print(f"Target Songs To Ingest:  {target_count:,}")
        print(f"Initial Existing Songs:  {len(self.seen_ids):,}")
        print(f"Seeded Creator Handles:  {len(self.handle_queue):,}")
        print(f"Target Catalog File:     {self.catalog_path}")
        print("-" * 65)

        newly_ingested = 0
        consecutive_errors = 0
        last_save_time = time.time()

        # 1. First drain Explore playlists
        while self.playlist_queue and newly_ingested < target_count:
            pid = self.playlist_queue.popleft()
            if pid in self.visited_playlists:
                continue
            self.visited_playlists.add(pid)
            print(f"\n[*] Scanning playlist {pid} ...")
            page = 1
            while page <= 30 and newly_ingested < target_count:
                url = f"https://studio-api.prod.suno.com/api/playlist/{pid}/?page={page}"
                req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
                try:
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        pdata = json.loads(resp.read().decode("utf-8"))
                    consecutive_errors = 0
                except Exception as ex:
                    print(f"[!] Playlist fetch notice ({pid}, p{page}): {ex}")
                    break

                clips = pdata.get("playlist_clips") or []
                if not clips:
                    break

                added_in_page = 0
                for item in clips:
                    c = item.get("clip") if isinstance(item, dict) else None
                    if not c:
                        continue
                    if self._ingest_clip(c, source=f"playlist_{pid}"):
                        newly_ingested += 1
                        added_in_page += 1
                        if newly_ingested >= target_count:
                            break

                print(f"    Playlist {pid[:8]}.. page {page}: +{added_in_page} new songs (total new: {newly_ingested}/{target_count})")
                if added_in_page == 0 or len(clips) < 4:
                    break
                page += 1
                time.sleep(0.2)

        # 2. Iterate creator handles and dynamic discovery
        while self.handle_queue and newly_ingested < target_count:
            handle = self.handle_queue.popleft().strip().lstrip("@")
            if not handle or handle in self.visited_handles:
                continue
            self.visited_handles.add(handle)

            page = 1
            max_pages = 25
            added_for_handle = 0

            while page <= max_pages and newly_ingested < target_count:
                url = (
                    f"https://studio-api.prod.suno.com/api/profiles/{urllib.parse.quote(handle)}"
                    f"?playlists_sort_by=created_at&clips_sort_by=created_at&page={page}"
                )
                req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
                try:
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        pdata = json.loads(resp.read().decode("utf-8"))
                    consecutive_errors = 0
                except urllib.error.HTTPError as h_err:
                    # 404 or 422 means profile private or doesn't exist
                    break
                except Exception as ex:
                    consecutive_errors += 1
                    if consecutive_errors > 10:
                        print(f"[!] Network pause: {ex}. Sleeping 3s ...")
                        time.sleep(3.0)
                    break

                clips = pdata.get("clips") or []
                if not clips:
                    break

                # Also queue any playlists created by this profile
                for pl in pdata.get("playlists") or []:
                    plid = pl.get("id")
                    if plid and plid not in self.visited_playlists:
                        self.playlist_queue.append(plid)

                page_new = 0
                for c in clips:
                    # Discover other handles mentioned in caption or collaborations
                    mentions = c.get("caption_mentions") or []
                    for m in mentions:
                        h_m = (m.get("handle") if isinstance(m, dict) else str(m)).lstrip("@")
                        if h_m and h_m not in self.visited_handles:
                            self.handle_queue.append(h_m)

                    if self._ingest_clip(c, source=f"profile_@{handle}"):
                        newly_ingested += 1
                        page_new += 1
                        added_for_handle += 1
                        if newly_ingested >= target_count:
                            break

                if page_new > 0 or page == 1:
                    print(f"    @{handle} p{page}: +{page_new} songs (total new: {newly_ingested:,}/{target_count:,} | queue: {len(self.handle_queue)})")

                if len(clips) < 4:
                    break

                page += 1
                time.sleep(0.18)

                # Periodic save every 50 songs or 30 seconds
                if time.time() - last_save_time > 30 or newly_ingested % 50 == 0:
                    self.save()
                    last_save_time = time.time()

        # Final save
        self.save()
        print("\n" + "=" * 65)
        print(f"[+] HARVEST COMPLETE: Ingested {newly_ingested:,} new tracks!")
        print(f"[+] Total Catalog Size: {len(self.catalog.all_records()):,} tracks")
        print("=" * 65)
        return newly_ingested

    def _ingest_clip(self, clip: dict[str, Any], source: str) -> bool:
        cid = str(clip.get("id") or "").lower().strip()
        if not cid or cid in self.seen_ids:
            return False

        meta = clip.get("metadata") if isinstance(clip.get("metadata"), dict) else {}
        lyrics = (clip.get("lyrics") or meta.get("prompt") or "").strip()
        prompt = (meta.get("prompt") or clip.get("prompt") or "").strip()
        title = (clip.get("title") or "").strip() or "Untitled Suno Track"
        tags_raw = meta.get("tags") or clip.get("tags") or clip.get("display_tags") or ""
        tags_str = str(tags_raw).strip()
        
        tags = [t.strip() for t in re.split(r"[,;/|]+", tags_str) if t.strip()]

        # Filter out completely empty clips (no title and no lyrics)
        if not lyrics and not prompt and not tags:
            return False

        rec_dict = {
            "song_id": cid,
            "title": title,
            "artist_id": clip.get("handle") or "",
            "artist_name": clip.get("display_name") or clip.get("handle") or "Suno Artist",
            "prompt": prompt,
            "lyrics": lyrics or prompt,
            "style_of_music": tags_str,
            "negative_prompt": str(meta.get("negative_tags") or ""),
            "tags": tags,
            "audio_url": clip.get("audio_url") or "",
            "video_url": clip.get("video_url") or "",
            "image_url": clip.get("image_url") or clip.get("image_large_url") or "",
            "duration_seconds": float(meta.get("duration")) if meta.get("duration") else None,
            "play_count": int(clip.get("play_count") or 0),
            "like_count": int(clip.get("upvote_count") or clip.get("like_count") or 0),
            "comment_count": int(clip.get("comment_count") or 0),
            "model_name": str(clip.get("model_name") or ""),
            "model_version": str(clip.get("major_model_version") or ""),
        }

        self.catalog.ingest(rec_dict, discovered_via=source)
        self.seen_ids.add(cid)
        self.processed_ids[cid] = {
            "title": title,
            "artist": rec_dict["artist_name"],
            "url": f"https://suno.com/song/{cid}",
            "processed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "ingested_harvest",
        }
        return True

    def save(self) -> None:
        """Persist catalog and tracker to disk, mirroring to dist/."""
        self.catalog.save()

        # Update tracker
        payload = {
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_processed": len(self.processed_ids),
            "processed_ids": self.processed_ids,
        }
        self.tracker_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tracker_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        # Mirror to dist
        dist_cat = Path("dist/models/suno_song_catalog.json")
        if dist_cat.parent.exists() and dist_cat.resolve() != self.catalog_path.resolve():
            try:
                import shutil
                shutil.copy2(self.catalog_path, dist_cat)
            except Exception:
                pass

        dist_tracker = Path("dist/models/auto_train_processed.json")
        if dist_tracker.parent.exists() and dist_tracker.resolve() != self.tracker_path.resolve():
            try:
                import shutil
                shutil.copy2(self.tracker_path, dist_tracker)
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Harvest 2,000+ new songs from Suno explore & trending feeds")
    parser.add_argument("--count", "-c", type=int, default=2000, help="Number of new songs to harvest")
    parser.add_argument("--catalog", type=str, default="models/suno_song_catalog.json", help="Target catalog path")
    args = parser.parse_args()

    harvester = SunoHarvester(catalog_path=args.catalog)
    harvested = harvester.harvest(target_count=args.count)
    return 0 if harvested >= args.count else 1


if __name__ == "__main__":
    raise SystemExit(main())
