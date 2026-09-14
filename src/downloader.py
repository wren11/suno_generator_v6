"""Suno song metadata scraper and audio downloader."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.catalog import song_id_from_url

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


@dataclass
class SunoSongPayload:
    song_id: str
    url: str
    title: str = ""
    prompt: str = ""
    lyrics: str = ""
    style_of_music: str = ""
    tags: list[str] = field(default_factory=list)
    artist_id: str = ""
    artist_name: str = ""
    audio_url: str = ""
    video_url: str = ""
    downloaded_audio_path: Path | None = None
    like_count: int = 0
    play_count: int = 0
    duration_seconds: float | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class SunoSongDownloader:
    """Extracts public song metadata and downloads progressive audio stream from Suno."""

    def __init__(self, output_dir: str | Path = "output/audio") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_song(self, song_url_or_id: str, *, download_audio: bool = True) -> SunoSongPayload:
        sid = song_id_from_url(song_url_or_id)
        if not sid and re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", song_url_or_id.strip(), re.I):
            sid = song_url_or_id.strip().lower()
        if not sid:
            raise ValueError(f"Could not extract valid Suno song UUID from: '{song_url_or_id}'")

        song_url = f"https://suno.com/song/{sid}"
        print(f"[*] Fetching Suno web page: {song_url} ...")
        html = self._fetch_html(song_url)
        raw_obj = self._parse_song_schema(html, sid)

        title = str(raw_obj.get("title") or "").strip()
        meta = raw_obj.get("metadata") or {}
        tags_str = str(meta.get("tags") or raw_obj.get("tags") or "")
        tags = [t.strip() for t in re.split(r"[,;/|]+", tags_str) if t.strip()]

        prompt = str(meta.get("prompt") or raw_obj.get("prompt") or "").strip()
        lyrics = str(raw_obj.get("lyrics") or meta.get("prompt") or "").strip()

        # Extract audio stream URL (prefer standard MP4 video_url as it contains clean AAC audio)
        audio_stream_url = str(raw_obj.get("video_url") or "").strip()
        if not audio_stream_url:
            media_urls = raw_obj.get("media_urls") or []
            for m in media_urls:
                u = str(m.get("url") or "")
                if u and ("mp4" in u or "mp3" in u or "m4a" in u):
                    audio_stream_url = u
                    break
            if not audio_stream_url and media_urls and media_urls[0].get("url"):
                audio_stream_url = str(media_urls[0]["url"])

        audio_path: Path | None = None
        if download_audio and audio_stream_url:
            ext = ".mp4" if ".mp4" in audio_stream_url else ".m4a"
            audio_filename = f"{sid}{ext}"
            target_path = self.output_dir / audio_filename
            print(f"[*] Downloading song audio: {audio_stream_url} -> {target_path} ...")
            self._download_file(audio_stream_url, target_path)
            audio_path = target_path
            print(f"[+] Downloaded audio ({target_path.stat().st_size // 1024} KB)")

        user = raw_obj.get("user") or {}
        handle = str(raw_obj.get("handle") or user.get("handle") or "").strip()
        display_name = str(raw_obj.get("display_name") or user.get("display_name") or "").strip()
        likes = int(raw_obj.get("upvote_count") or raw_obj.get("like_count") or 0)
        plays = int(raw_obj.get("play_count") or 0)
        dur = meta.get("duration") or raw_obj.get("duration")
        dur_f = float(dur) if dur is not None else None

        return SunoSongPayload(
            song_id=sid,
            url=song_url,
            title=title,
            prompt=prompt,
            lyrics=lyrics,
            style_of_music=tags_str,
            tags=tags,
            artist_id=handle,
            artist_name=display_name,
            audio_url=audio_stream_url,
            video_url=str(raw_obj.get("video_url") or ""),
            downloaded_audio_path=audio_path,
            like_count=likes,
            play_count=plays,
            duration_seconds=dur_f,
            raw_metadata=raw_obj,
        )

    def _fetch_html(self, url: str) -> str:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    def _parse_song_schema(self, html: str, sid: str) -> dict[str, Any]:
        """Extract the Next.js embedded JSON object for this song."""
        idx = html.find(f'\\"id\\":\\"{sid}\\"')
        if idx == -1:
            idx = html.find(sid)
        if idx != -1:
            start = html.rfind('{', 0, idx)
            depth = 0
            in_quote = False
            escape = False
            end = -1
            for i in range(start, len(html)):
                c = html[i]
                if escape:
                    escape = False
                    continue
                if c == '\\':
                    escape = True
                    continue
                if c == '"':
                    in_quote = not in_quote
                    continue
                if not in_quote:
                    if c == '{':
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
            if end > start:
                raw = html[start:end]
                try:
                    unescaped = raw.encode().decode("unicode_escape")
                    return json.loads(unescaped)
                except Exception:
                    pass
                try:
                    fixed = raw.replace('\\"', '"').replace('\\\\', '\\')
                    return json.loads(fixed)
                except Exception:
                    pass

        # Fallback regex search
        title_m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        title = title_m.group(1) if title_m else "Suno Track"
        desc_m = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        desc = desc_m.group(1) if desc_m else ""
        return {"id": sid, "title": title, "prompt": desc}

    def fetch_profile_clips(self, handle: str, max_pages: int = 50) -> list[dict]:
        """Fetch all public song clips from a Suno user profile (e.g. @wren)."""
        clean_handle = handle.strip().lstrip("@")
        if not clean_handle:
            return []
        import urllib.parse
        import time

        clips: list[dict] = []
        seen_ids: set[str] = set()
        page = 1

        print(f"[*] Fetching Suno profile clips for: @{clean_handle} ...")
        while page <= max_pages:
            url = (
                f"https://studio-api.prod.suno.com/api/profiles/{urllib.parse.quote(clean_handle)}"
                f"?playlists_sort_by=created_at&clips_sort_by=created_at&page={page}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print(f"[!] Error fetching profile page {page}: {e}")
                break

            page_clips = data.get("clips") or []
            if not page_clips:
                break

            new_count = 0
            for c in page_clips:
                cid = str(c.get("id") or "").lower()
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    clips.append(c)
                    new_count += 1

            print(f"    Page {page}: +{new_count} clips (total: {len(clips)})")
            if new_count == 0 or len(page_clips) < 4:
                break
            page += 1
            time.sleep(0.25)

        print(f"[+] Total clips fetched for @{clean_handle}: {len(clips)}")
        return clips

    def _download_file(self, url: str, dest: Path) -> None:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as fh:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                fh.write(chunk)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m src.downloader <suno_song_url_or_id> [output_dir]")
        return 1
    target = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "output/audio"
    dl = SunoSongDownloader(out_dir)
    res = dl.fetch_song(target)
    print(f"\n[+] Success: {res.title} ({res.song_id})")
    print(f"    Style: {res.style_of_music}")
    print(f"    Likes: {res.like_count} | Plays: {res.play_count}")
    print(f"    Audio saved: {res.downloaded_audio_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
