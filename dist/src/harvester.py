"""High-throughput Multi-threaded Suno Trending & Explore Harvester.

Fetches trending, explore, and top creator tracks from Suno's live APIs,
filtering strictly for songs with 100+ upvotes/likes and ingesting them into
the song catalog until target quota is reached.
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import datetime
import json
import os
import re
import sys
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.catalog import SongCatalogStore

# Safe Windows UTF-8 console output with unbuffered line output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

INITIAL_HANDLES = [
    "wren", "rushyrush15", "rustyspork", "jackempire", "pepek39501",
    "ladydevil", "nrv13", "lunasolaris", "dmistebaev", "airockstar72",
    "wes", "atmta", "donut", "jacktempchin", "illangelo", "oliverstone",
    "sheezy", "rickyfonse", "jayvenom", "artdiva", "cmd_play", "gnerka", "tooone",
    "stringentmonotone054", "deliminebe", "alexandredurbuis", "spaggyg", "soniqa",
    "its_carocaro_baby", "joyousmck", "ebrg", "tagliuz", "marcxiz", "aimagician",
    "namestaken", "restina", "foggy", "shirokurono", "wraex", "coastridge",
    "tarja_ravenveil", "eddissoncom", "freshaudioengineer138", "ao_chanko",
    "busystudio", "rom_jeremy666", "moonrider", "otherworldlydrumstick919",
    "modernbard", "ntroy", "sukusapoono", "jonathanfly", "sonicmystics", "raretour9406",
    "stepya2014", "orxan29111309", "arionxeasylynx", "evolutio01", "foundinworship777",
    "gestuncom", "olegmitin689", "valentina_zorkich", "immutableexpression009",
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
    "e0816e45-29ba-4748-89c4-8ee8a7ff7f6b",  # Contest Remix She's A Little Bit
    "1ed827f7-168c-4e07-bfa0-90444fe3afed",  # Human Sounds Submissions
    "01848471-c34f-4ada-9aa0-0dcc223a89bb",  # Human Sounds Winners
    "8f091041-358e-44cf-a4b2-d87ea92465de",  # Summer Stereo
    "21703e42-d20e-4bad-8c80-138923ac8865",  # Glass Submissions
    "d3908ec7-25cc-4ec8-bd73-168b4289acb5",  # Glass Winners
    "8b9baa1a-ad28-4163-92b3-ca0324f4df20",  # JasonMartin Submissions
    "69a6432d-2b23-4e08-82f7-9a313f8e42d0",  # JasonMartin Winners
    "9fdab699-2874-4f13-b946-d2838282f3a3",  # Lonely Nights Submissions
    "5a972310-ecff-4db6-b61e-f1615c4a03b1",  # Lonely Nights Winners
    "4189a552-ae58-4d81-a763-ac4c54d2badb",  # Only Love Knows Submissions
    "10aa7ef9-8aea-4c12-b075-060aebf3759a",  # Only Love Knows Winners
    "e1bdbc61-b5b8-4b6c-99bc-b7a622e14053",  # Illangelo Submissions
    "af414416-e4dd-4ca2-b1d3-cabadcd0d04e",  # Illangelo Winners
    "3c4bfb96-1524-4fa4-a650-8e2f71975bb5",  # Happy Living Room Submissions
    "ae010b94-a0ed-45bd-bdba-e0bf8e2fa546",  # Happy Living Room Winners
    "8944399b-d955-4281-9d0c-1069c5210f6e",  # ImOliver Stone Submissions
    "06017b2d-5aad-4917-a3ed-f3a080d34045",  # ImOliver Stone Winners
    "bb031e22-ebd7-4962-bbf5-dbe612fc2bf1",  # September Artist Showcase
    "f2226d36-af7f-4b00-8ef7-5d17985138b0",  # August Artist Remix Challenge
    "537877ee-110d-4668-ad07-4576c04c9320",  # August Artist Showcase
    "f2f118e8-e411-49b3-b7df-76940e1a5fa6",  # August Remix #2
]

GENRES = [
    "pop", "rock", "hiphop", "rap", "metal", "synthwave", "retrowave", "edm",
    "techno", "house", "lofi", "chill", "folk", "country", "blues", "jazz",
    "punk", "reggae", "soul", "ambient", "classical", "trap", "rnb", "indie",
    "disco", "funk", "electronic", "acoustic", "darkwave", "vaporwave", "phonk",
    "cyberpunk", "soundtrack", "cinematic", "epic", "ballad"
]

MODIFIERS = [
    "music", "studio", "records", "beats", "sound", "sounds", "prod", "producer",
    "audio", "band", "official", "project", "songs", "ai", "art", "artist",
    "vibes", "fm", "radio", "hits", "master", "club", "lab", "wave"
]

NUM_SUFFIXES = ["", "1", "2", "10", "12", "15", "20", "24", "25", "69", "77", "88", "99", "100", "777", "888", "999", "2024", "2025"]


def _create_http_session() -> requests.Session:
    """Create a persistent requests.Session with connection pooling and auto-retries."""
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    retries = Retry(total=2, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=16, pool_maxsize=16)
    session.mount("https://", adapter)
    return session


class SunoHarvester:
    """High-throughput multi-threaded Suno song harvester."""

    def __init__(
        self,
        catalog_path: str | Path = "models/suno_song_catalog.json",
        tracker_path: str | Path = "models/auto_train_processed.json",
    ) -> None:
        self.catalog_path = Path(catalog_path)
        self.tracker_path = Path(tracker_path)
        self.catalog = SongCatalogStore(self.catalog_path)
        self.lock = threading.Lock()

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
                print(f"[!] Warning reading tracker: {ex}", flush=True)

        # Queues for graph traversal
        self.handle_queue: collections.deque[str] = collections.deque()
        self.visited_handles: set[str] = set()
        self.playlist_queue: collections.deque[str] = collections.deque()
        self.visited_playlists: set[str] = set()

        for h in INITIAL_HANDLES:
            if h not in self.handle_queue:
                self.handle_queue.append(h)

        for p in INITIAL_PLAYLISTS:
            self.playlist_queue.append(p)

        # Seed top creator handles from existing catalog ranked by upvotes
        handle_likes: dict[str, list[int]] = collections.defaultdict(list)
        for rec in self.catalog.all_records():
            h = (rec.artist_id or "").strip().lstrip("@")
            if h:
                handle_likes[h].append(rec.external_like_count or 0)

        ranked_handles = sorted(
            handle_likes.keys(),
            key=lambda h: (sum(1 for l in handle_likes[h] if l >= 100), max(handle_likes[h])),
            reverse=True,
        )
        for h in ranked_handles:
            if h not in self.handle_queue:
                self.handle_queue.append(h)

        # Generate systematic music handles
        for g in GENRES:
            for m in MODIFIERS:
                for n in NUM_SUFFIXES[:4]:
                    self.handle_queue.append(f"{g}_{m}{n}")
                    self.handle_queue.append(f"{g}{m}{n}")

    def _fetch_trending_feed(self, session: requests.Session) -> list[dict]:
        url = "https://studio-api-prod.suno.com/api/unified/feed"
        clips: list[dict] = []
        payload = {"feed_id": "trending", "page_size": 50}
        try:
            resp = session.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                for it in data.get("feed", {}).get("items", []):
                    c = it.get("content_item") or it.get("clip") or {}
                    if c:
                        clips.append(c)
        except Exception as ex:
            print(f"[!] Notice fetching unified feed: {ex}", flush=True)
        return clips

    def harvest(self, target_count: int = 5000, min_likes: int = 100, workers: int = 14) -> int:
        print("=" * 65, flush=True)
        print("  SUNO HIGH-THROUGHPUT TRENDING & EXPLORE HARVESTER", flush=True)
        print("=" * 65, flush=True)
        print(f"Target Songs To Ingest:    {target_count:,}", flush=True)
        print(f"Minimum Upvotes/Likes:     {min_likes}+", flush=True)
        print(f"Concurrent Worker Threads: {workers}", flush=True)
        print(f"Initial Existing Songs:    {len(self.seen_ids):,}", flush=True)
        print(f"Seeded Creator Handles:    {len(self.handle_queue):,}", flush=True)
        print(f"Seeded Playlists:          {len(self.playlist_queue):,}", flush=True)
        print(f"Target Catalog File:       {self.catalog_path}", flush=True)
        print("-" * 65, flush=True)

        newly_ingested = 0
        last_save_time = time.time()
        main_session = _create_http_session()

        # 1. Drain Unified Trending Feed
        print("\n[*] Fetching Suno Unified Trending Feed ...", flush=True)
        trending_clips = self._fetch_trending_feed(main_session)
        for c in trending_clips:
            h_t = (c.get("handle") or "").strip().lstrip("@")
            if h_t and h_t not in self.visited_handles:
                self.handle_queue.append(h_t)
            if self._ingest_clip(c, source="feed_trending", min_likes=min_likes):
                newly_ingested += 1
                if newly_ingested >= target_count:
                    break
        print(f"    Trending feed: +{newly_ingested} songs with {min_likes}+ likes", flush=True)

        # 2. Concurrent worker task covering playlists and creators
        print(f"\n[*] Starting concurrent crawl with {workers} worker threads ...", flush=True)

        def worker_task() -> None:
            nonlocal newly_ingested, last_save_time
            thread_session = _create_http_session()

            while newly_ingested < target_count:
                item_type = None
                target_item = None

                with self.lock:
                    if newly_ingested >= target_count:
                        return
                    # Prioritize playlists if available
                    if self.playlist_queue:
                        item_type = "playlist"
                        target_item = self.playlist_queue.popleft()
                        if target_item in self.visited_playlists:
                            continue
                        self.visited_playlists.add(target_item)
                    elif self.handle_queue:
                        item_type = "handle"
                        target_item = self.handle_queue.popleft().strip().lstrip("@")
                        if not target_item or target_item in self.visited_handles:
                            continue
                        self.visited_handles.add(target_item)
                    else:
                        return

                if item_type == "playlist":
                    _crawl_playlist(thread_session, target_item, min_likes, target_count)
                elif item_type == "handle":
                    _crawl_handle(thread_session, target_item, min_likes, target_count)

        def _crawl_playlist(session: requests.Session, pid: str, min_likes: int, target_count: int) -> None:
            nonlocal newly_ingested, last_save_time
            page = 1
            max_pages = 10
            added_for_pl = 0
            while page <= max_pages and newly_ingested < target_count:
                url = f"https://studio-api.prod.suno.com/api/playlist/{pid}/?page={page}"
                try:
                    resp = session.get(url, timeout=10)
                    if resp.status_code != 200:
                        break
                    pdata = resp.json()
                except Exception:
                    break

                clips = pdata.get("playlist_clips") or []
                if not clips:
                    break

                for it in clips:
                    c = it.get("clip") if isinstance(it, dict) else None
                    if not c:
                        continue
                    h_p = (c.get("handle") or "").strip().lstrip("@")
                    if h_p and h_p not in self.visited_handles:
                        with self.lock:
                            self.handle_queue.append(h_p)

                    with self.lock:
                        if newly_ingested >= target_count:
                            return
                        if self._ingest_clip(c, source=f"playlist_{pid[:8]}", min_likes=min_likes):
                            newly_ingested += 1
                            added_for_pl += 1

                if len(clips) < 4:
                    break
                page += 1
                time.sleep(0.04)

            if added_for_pl > 0:
                with self.lock:
                    print(f"    [PL] {pid[:8]}.. : +{added_for_pl} ({min_likes}+ likes) | Total: {newly_ingested:,}/{target_count:,} | H-Queue: {len(self.handle_queue):,}", flush=True)
                    if time.time() - last_save_time > 15 or newly_ingested % 50 == 0:
                        self.save()
                        last_save_time = time.time()

        def _crawl_handle(session: requests.Session, handle: str, min_likes: int, target_count: int) -> None:
            nonlocal newly_ingested, last_save_time
            page = 1
            max_pages = 20
            added_for_handle = 0

            while page <= max_pages and newly_ingested < target_count:
                url = (
                    f"https://studio-api.prod.suno.com/api/profiles/{urllib.parse.quote(handle)}"
                    f"?playlists_sort_by=created_at&clips_sort_by=upvote_count&page={page}"
                )
                try:
                    resp = session.get(url, timeout=10)
                    if resp.status_code != 200:
                        break
                    pdata = resp.json()
                except Exception:
                    break

                clips = pdata.get("clips") or []
                if not clips:
                    break

                for pl in pdata.get("playlists") or []:
                    plid = pl.get("id")
                    if plid and plid not in self.visited_playlists:
                        with self.lock:
                            self.playlist_queue.append(plid)

                stop_handle = False
                for c in clips:
                    upvotes = int(c.get("upvote_count") or c.get("like_count") or 0)

                    mentions = c.get("caption_mentions") or []
                    for m in mentions:
                        h_m = (m.get("handle") if isinstance(m, dict) else str(m)).lstrip("@")
                        if h_m and h_m not in self.visited_handles:
                            with self.lock:
                                self.handle_queue.append(h_m)

                    if upvotes < min_likes:
                        stop_handle = True
                        break

                    with self.lock:
                        if newly_ingested >= target_count:
                            return
                        if self._ingest_clip(c, source=f"profile_@{handle}", min_likes=min_likes):
                            newly_ingested += 1
                            added_for_handle += 1

                if stop_handle or len(clips) < 4:
                    break
                page += 1
                time.sleep(0.04)

            if added_for_handle > 0:
                with self.lock:
                    print(f"    [+] @{handle:<18}: +{added_for_handle} ({min_likes}+ likes) | Total: {newly_ingested:,}/{target_count:,} | PL-Queue: {len(self.playlist_queue):,} | H-Queue: {len(self.handle_queue):,}", flush=True)
                    if time.time() - last_save_time > 15 or newly_ingested % 50 == 0:
                        self.save()
                        last_save_time = time.time()

        if newly_ingested < target_count:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(worker_task) for _ in range(workers)]
                concurrent.futures.wait(futures)

        # Final save
        self.save()
        print("\n" + "=" * 65, flush=True)
        print(f"[+] HARVEST COMPLETE: Ingested {newly_ingested:,} new tracks with {min_likes}+ likes!", flush=True)
        print(f"[+] Total Catalog Size: {len(self.catalog.all_records()):,} tracks", flush=True)
        print("=" * 65, flush=True)
        return newly_ingested

    def _ingest_clip(self, clip: dict[str, Any], source: str, min_likes: int = 0) -> bool:
        cid = str(clip.get("id") or "").lower().strip()
        if not cid or cid in self.seen_ids:
            return False

        upvotes = int(clip.get("upvote_count") or clip.get("like_count") or 0)
        if upvotes < min_likes:
            return False

        meta = clip.get("metadata") if isinstance(clip.get("metadata"), dict) else {}
        lyrics = (clip.get("lyrics") or meta.get("prompt") or "").strip()
        prompt = (meta.get("prompt") or clip.get("prompt") or "").strip()
        title = (clip.get("title") or "").strip() or "Untitled Suno Track"
        tags_raw = meta.get("tags") or clip.get("tags") or clip.get("display_tags") or ""
        tags_str = str(tags_raw).strip()
        
        tags = [t.strip() for t in re.split(r"[,;/|]+", tags_str) if t.strip()]

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
            "like_count": upvotes,
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
            "like_count": upvotes,
        }
        return True

    def save(self) -> None:
        """Persist catalog and tracker to disk, mirroring to dist/."""
        self.catalog.save()

        payload = {
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_processed": len(self.processed_ids),
            "processed_ids": self.processed_ids,
        }
        self.tracker_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tracker_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

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
    parser = argparse.ArgumentParser(description="Harvest 5,000+ new songs with 100+ likes from Suno")
    parser.add_argument("--count", "-c", type=int, default=5000, help="Number of new songs to harvest")
    parser.add_argument("--min-likes", "-l", type=int, default=100, help="Minimum likes/upvotes required per track")
    parser.add_argument("--workers", "-w", type=int, default=14, help="Number of concurrent workers")
    parser.add_argument("--catalog", type=str, default="models/suno_song_catalog.json", help="Target catalog path")
    args = parser.parse_args()

    harvester = SunoHarvester(catalog_path=args.catalog)
    harvested = harvester.harvest(target_count=args.count, min_likes=args.min_likes, workers=args.workers)
    return 0 if harvested >= args.count else 1


if __name__ == "__main__":
    raise SystemExit(main())
