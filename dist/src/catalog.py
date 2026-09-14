"""Persistent song catalog — lyrics, tags, styles, prompts, derived features, engagement."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.features import derive_song_features, slim_raw_feed_json, unwrap_clip_metadata

_SONG_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.I,
)

_RICH_TEXT_FIELDS = (
    "title",
    "prompt",
    "lyrics",
    "gpt_description",
    "description",
    "style_of_music",
    "negative_prompt",
    "combined_creative_text",
)
_LIST_FIELDS = ("tags", "genres", "styles", "derived_prompt_tokens", "structure_tags", "seed_keyword_hits", "novel_keywords")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def song_id_from_url(url: str) -> str:
    if not url:
        return ""
    m = _SONG_UUID_RE.search(url)
    return m.group(0).lower() if m else ""


@dataclass
class SongRecord:
    song_id: str
    url: str = ""
    title: str = ""
    prompt: str = ""
    lyrics: str = ""
    gpt_description: str = ""
    description: str = ""
    style_of_music: str = ""
    negative_prompt: str = ""
    combined_creative_text: str = ""
    tags: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    artist_id: str = ""
    artist_name: str = ""
    audio_url: str = ""
    image_url: str = ""
    video_url: str = ""
    duration_seconds: float | None = None
    external_like_count: int = 0
    play_count: int | None = None
    comment_count: int | None = None
    model_name: str = ""
    model_version: str = ""
    is_instrumental: bool | None = None
    create_mode: str = ""
    status: str = ""
    discovered_via: str = ""
    observation_count: int = 0
    first_seen_at: str = ""
    last_seen_at: str = ""
    last_engaged_at: str = ""
    engaged_liked: bool = False
    engaged_commented: bool = False
    engaged_followed: bool = False
    # derived
    derived_style_signature: str = ""
    derived_traction_tier: str = ""
    derived_is_instrumental: bool | None = None
    lyric_line_count: int = 0
    lyric_word_count: int = 0
    lyric_avg_line_length: float = 0.0
    rhyme_density: float = 0.0
    structure_tags: list[str] = field(default_factory=list)
    derived_prompt_tokens: list[str] = field(default_factory=list)
    seed_keyword_hits: list[str] = field(default_factory=list)
    novel_keywords: list[str] = field(default_factory=list)
    seed_coverage_ratio: float = 0.0
    authorship_label: str = "mixed_or_unclear"
    authorship_ai_score: float = 0.5
    authorship_handwritten_score: float = 0.5
    authorship_signals: list[str] = field(default_factory=list)
    raw_feed_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SongRecord:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        kwargs = {k: data[k] for k in known if k in data}
        return cls(**kwargs)


def _richness(text: str) -> int:
    return len((text or "").strip())


def _merge_lists(existing: list[str], incoming: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in list(existing) + list(incoming):
        norm = str(item).strip().lower()[:80]
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out[:40]


def _pick_richer(old: str, new: str) -> str:
    o = (old or "").strip()
    n = (new or "").strip()
    if not n:
        return o
    if not o:
        return n
    return n if len(n) > len(o) else o


def _pick_max_int(old: int | None, new: int | None) -> int | None:
    if new is None:
        return old
    if old is None:
        return new
    return max(old, new)


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_feed_row(row: dict[str, Any], *, base_url: str = "https://suno.com") -> dict[str, Any]:
    """Map feed API / DOM row into catalog ingest payload."""
    row = unwrap_clip_metadata(row if isinstance(row, dict) else {})
    sid = str(row.get("id") or row.get("song_id") or "").strip()
    url = str(row.get("url") or row.get("href") or "").strip()
    if not sid and url:
        sid = song_id_from_url(url)
    if not url and sid:
        url = f"{base_url.rstrip('/')}/song/{sid}"
    likes = row.get("like_count", row.get("external_like_count", row.get("upvote_count")))
    try:
        like_int = int(likes) if likes is not None else 0
    except (TypeError, ValueError):
        like_int = 0
    duration = row.get("duration") or row.get("duration_seconds")
    try:
        dur_f = float(duration) if duration is not None else None
    except (TypeError, ValueError):
        dur_f = None
    user = row.get("user") or row.get("artist") or {}
    artist_id = str(row.get("artist_id") or row.get("handle") or "").strip().lower()
    artist_name = str(row.get("artist_name") or row.get("display_name") or row.get("author_display") or "").strip()
    if isinstance(user, dict):
        artist_id = artist_id or str(user.get("handle") or user.get("username") or "").strip().lower()
        artist_name = artist_name or str(user.get("display_name") or user.get("name") or "").strip()
    instrumental = row.get("is_instrumental")
    if instrumental is not None:
        instrumental = bool(instrumental)
    style = str(row.get("style_of_music") or row.get("style") or "")
    tags = list(row.get("tags") or [])
    if style and not tags:
        tags = [t.strip() for t in re.split(r"[,;/|]+", style) if t.strip()][:30]
    return {
        "song_id": sid,
        "url": url,
        "title": str(row.get("title") or row.get("name") or ""),
        "prompt": str(row.get("prompt") or ""),
        "lyrics": str(row.get("lyrics") or ""),
        "gpt_description": str(row.get("gpt_description") or ""),
        "description": str(row.get("description") or ""),
        "style_of_music": style,
        "negative_prompt": str(row.get("negative_prompt") or ""),
        "tags": tags,
        "genres": list(row.get("genres") or []),
        "styles": list(row.get("styles") or []),
        "artist_id": artist_id,
        "artist_name": artist_name[:120],
        "audio_url": str(row.get("audio_url") or ""),
        "image_url": str(row.get("image_url") or row.get("image_large_url") or ""),
        "video_url": str(row.get("video_url") or ""),
        "duration_seconds": dur_f,
        "external_like_count": like_int,
        "play_count": _safe_int(row.get("play_count")),
        "comment_count": _safe_int(row.get("comment_count")),
        "model_name": str(row.get("model_name") or row.get("model") or ""),
        "model_version": str(row.get("major_model_version") or row.get("model_version") or ""),
        "is_instrumental": instrumental,
        "create_mode": str(row.get("type") or row.get("create_mode") or ""),
        "status": str(row.get("status") or ""),
        "discovered_via": str(row.get("discovered_via") or "api_feed"),
        "raw_feed_snapshot": slim_raw_feed_json(row) if row.get("id") else {},
    }


def resolve_catalog_path(path: str | Path | None = None) -> Path:
    """Find the authoritative catalog file across root, dist, and parent folders."""
    if path:
        p = Path(path)
        if p.exists() and p.is_file() and p.stat().st_size > 100_000:
            return p
    candidates = [
        Path(path) if path else None,
        Path("dist/models/suno_song_catalog.json"),
        Path("models/suno_song_catalog.json"),
        Path("../models/suno_song_catalog.json"),
        Path("../dist/models/suno_song_catalog.json"),
        Path(__file__).resolve().parent.parent / "dist" / "models" / "suno_song_catalog.json",
        Path(__file__).resolve().parent.parent / "models" / "suno_song_catalog.json",
    ]
    best: Path | None = None
    best_size = -1
    for c in candidates:
        if c and c.exists() and c.is_file():
            sz = c.stat().st_size
            if sz > best_size:
                best_size = sz
                best = c
    if best and best_size > 100_000:
        return best
    return Path(path or "models/suno_song_catalog.json")


class SongCatalogStore:
    """JSON-backed catalog of discovered songs with merge + derived features."""

    def __init__(self, path: str | Path = "suno_song_catalog.json") -> None:
        self.path = resolve_catalog_path(path)
        self._data: dict[str, Any] = self._load()

    def _empty(self) -> dict[str, Any]:
        return {
            "version": 1,
            "updated_at": _utc_now(),
            "stats": {
                "total_songs": 0,
                "with_lyrics": 0,
                "with_prompt": 0,
                "with_tags": 0,
                "engaged": 0,
                "high_traction": 0,
                "likely_ai": 0,
                "likely_handwritten": 0,
                "mixed_or_unclear": 0,
            },
            "songs": {},
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                raw.setdefault("version", 1)
                raw.setdefault("songs", {})
                raw.setdefault("stats", {})
                return raw
        except Exception:
            pass
        return self._empty()

    def save(self) -> None:
        self._recompute_stats()
        self._data["updated_at"] = _utc_now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(self._data, indent=2, ensure_ascii=False)
        self.path.write_text(serialized, encoding="utf-8")

        # Mirror save to sister models directories if present
        for candidate_dir in [
            Path(__file__).resolve().parent.parent / "models",
            Path(__file__).resolve().parent.parent / "dist" / "models",
        ]:
            if candidate_dir.exists() and candidate_dir != self.path.parent:
                mirror_path = candidate_dir / self.path.name
                try:
                    mirror_path.write_text(serialized, encoding="utf-8")
                except Exception:
                    pass

    def _recompute_stats(self) -> None:
        songs: dict = self._data.get("songs") or {}
        stats = {
            "total_songs": len(songs),
            "with_lyrics": 0,
            "with_prompt": 0,
            "with_tags": 0,
            "engaged": 0,
            "high_traction": 0,
            "likely_ai": 0,
            "likely_handwritten": 0,
            "mixed_or_unclear": 0,
        }
        for rec in songs.values():
            if not isinstance(rec, dict):
                continue
            if (rec.get("lyrics") or "").strip():
                stats["with_lyrics"] += 1
            if (rec.get("prompt") or rec.get("style_of_music") or "").strip():
                stats["with_prompt"] += 1
            if rec.get("tags"):
                stats["with_tags"] += 1
            if rec.get("engaged_liked") or rec.get("engaged_commented") or rec.get("engaged_followed"):
                stats["engaged"] += 1
            tier = rec.get("derived_traction_tier") or ""
            if tier in ("high", "viral"):
                stats["high_traction"] += 1
            label = str(rec.get("authorship_label") or "mixed_or_unclear")
            if label in stats:
                stats[label] += 1
            else:
                stats["mixed_or_unclear"] += 1
        self._data["stats"] = stats

    def get(self, song_id: str) -> SongRecord | None:
        raw = (self._data.get("songs") or {}).get(song_id)
        if not isinstance(raw, dict):
            return None
        return SongRecord.from_dict(raw)

    def all_records(self) -> list[SongRecord]:
        songs = self._data.get("songs") or {}
        out: list[SongRecord] = []
        for raw in songs.values():
            if isinstance(raw, dict):
                out.append(SongRecord.from_dict(raw))
        return out

    def ingest(self, payload: dict[str, Any], *, discovered_via: str = "") -> SongRecord | None:
        sid = str(payload.get("song_id") or "").strip().lower()
        url = str(payload.get("url") or "").strip()
        if not sid:
            sid = song_id_from_url(url)
        if not sid:
            return None
        if not url:
            url = f"https://suno.com/song/{sid}"
        if discovered_via:
            payload = {**payload, "discovered_via": discovered_via}

        bucket: dict = self._data.setdefault("songs", {})
        existing_raw = bucket.get(sid)
        if isinstance(existing_raw, dict):
            merged = self._merge(existing_raw, payload)
        else:
            merged = dict(payload)
            merged["song_id"] = sid
            merged["url"] = url
            merged["first_seen_at"] = _utc_now()
            merged["observation_count"] = 0

        merged["song_id"] = sid
        merged["url"] = url
        merged["last_seen_at"] = _utc_now()
        merged["observation_count"] = int(merged.get("observation_count") or 0) + 1

        derived = derive_song_features(merged)
        for k, v in derived.items():
            merged[k] = v

        bucket[sid] = merged
        return SongRecord.from_dict(merged)

    def ingest_feed_row(self, row: dict[str, Any], *, base_url: str = "https://suno.com", discovered_via: str = "api_feed") -> SongRecord | None:
        payload = normalize_feed_row(row, base_url=base_url)
        payload["discovered_via"] = discovered_via
        return self.ingest(payload)

    def record_engagement(
        self,
        song_id: str,
        *,
        liked: bool = False,
        commented: bool = False,
        followed: bool = False,
    ) -> None:
        sid = (song_id or "").strip().lower()
        if not sid:
            return
        bucket: dict = self._data.setdefault("songs", {})
        raw = bucket.get(sid)
        if not isinstance(raw, dict):
            return
        raw["last_engaged_at"] = _utc_now()
        if liked:
            raw["engaged_liked"] = True
        if commented:
            raw["engaged_commented"] = True
        if followed:
            raw["engaged_followed"] = True
        raw["last_seen_at"] = _utc_now()

    def reprocess_all(self) -> int:
        """Re-run feature extraction for every stored song and persist the result."""
        songs: dict = self._data.setdefault("songs", {})
        count = 0
        for sid, raw in list(songs.items()):
            if not isinstance(raw, dict):
                continue
            merged = dict(raw)
            merged["song_id"] = sid
            merged["url"] = str(merged.get("url") or f"https://suno.com/song/{sid}")
            derived = derive_song_features(merged)
            for k, v in derived.items():
                merged[k] = v
            songs[sid] = merged
            count += 1
        self.save()
        return count

    def _merge(self, existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        out = dict(existing)
        for key in _RICH_TEXT_FIELDS:
            if key in incoming:
                out[key] = _pick_richer(str(out.get(key) or ""), str(incoming.get(key) or ""))
        for key in _LIST_FIELDS:
            if key in incoming:
                out[key] = _merge_lists(list(out.get(key) or []), list(incoming.get(key) or []))
        for key in (
            "artist_id",
            "artist_name",
            "audio_url",
            "image_url",
            "video_url",
            "model_name",
            "model_version",
            "create_mode",
            "status",
            "negative_prompt",
        ):
            if incoming.get(key):
                out[key] = incoming[key]
        out["external_like_count"] = max(
            int(out.get("external_like_count") or 0),
            int(incoming.get("external_like_count") or incoming.get("like_count") or 0),
        )
        out["play_count"] = _pick_max_int(out.get("play_count"), incoming.get("play_count"))
        out["comment_count"] = _pick_max_int(out.get("comment_count"), incoming.get("comment_count"))
        if incoming.get("duration_seconds") is not None:
            out["duration_seconds"] = incoming["duration_seconds"]
        if incoming.get("is_instrumental") is not None:
            out["is_instrumental"] = incoming["is_instrumental"]
        via = str(incoming.get("discovered_via") or "")
        if via and via not in str(out.get("discovered_via") or ""):
            prev = str(out.get("discovered_via") or "")
            out["discovered_via"] = f"{prev},{via}" if prev else via
        snap = incoming.get("raw_feed_snapshot")
        if isinstance(snap, dict) and snap:
            prev_snap = out.get("raw_feed_snapshot") or {}
            if isinstance(prev_snap, dict):
                out["raw_feed_snapshot"] = {**prev_snap, **snap}
            else:
                out["raw_feed_snapshot"] = snap
        return out

    def export_jsonl(self, dest: str | Path, *, min_likes: int = 0) -> int:
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        n = 0
        with dest_path.open("w", encoding="utf-8") as fh:
            for rec in self.all_records():
                if rec.external_like_count < min_likes:
                    continue
                fh.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
                n += 1
        return n

    def format_stats_report(self) -> str:
        stats = self._data.get("stats") or {}
        songs = self.all_records()
        with_lyrics_pct = 0
        if stats.get("total_songs"):
            with_lyrics_pct = round(100 * stats.get("with_lyrics", 0) / stats["total_songs"], 1)
        top_styles: dict[str, int] = {}
        for rec in songs:
            for tag in rec.tags[:5]:
                top_styles[tag] = top_styles.get(tag, 0) + 1
        top5 = sorted(top_styles.items(), key=lambda x: (-x[1], x[0]))[:8]
        lines = [
            "--- SONG CATALOG / DATASET ---",
            f"  file: {self.path}",
            f"  total songs: {stats.get('total_songs', 0)} | with lyrics: {stats.get('with_lyrics', 0)} ({with_lyrics_pct}%)",
            f"  with prompt/style: {stats.get('with_prompt', 0)} | with tags: {stats.get('with_tags', 0)}",
            f"  engaged: {stats.get('engaged', 0)} | high traction: {stats.get('high_traction', 0)}",
            f"  likely AI: {stats.get('likely_ai', 0)} | likely handwritten: {stats.get('likely_handwritten', 0)} | mixed/unclear: {stats.get('mixed_or_unclear', 0)}",
        ]
        if top5:
            lines.append("  top tags in catalog:")
            for tag, cnt in top5:
                lines.append(f"    + {tag}: {cnt}")
        lines.append("------------------------------")
        return "\n".join(lines)
