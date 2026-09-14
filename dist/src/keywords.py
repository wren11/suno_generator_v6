"""Track Suno prompts/tags/styles; report popular vs unused English keywords and style packs."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Curated English seeds for genre/mood/instrument/production vocabulary (lowercase).
ENGLISH_SEED_KEYWORDS: frozenset[str] = frozenset(
    kw.lower()
    for kw in (
        "acoustic", "ambient", "anthem", "atmospheric", "bass", "beat", "blues", "bouncy",
        "breakbeat", "chill", "cinematic", "classical", "country", "dance", "dark",
        "deep", "disco", "downtempo", "dreamy", "drill", "dubstep", "edm", "electro",
        "electronic", "emotional", "energetic", "epic", "experimental", "fast", "folk",
        "funk", "fusion", "future", "gospel", "guitar", "happy", "hard", "hardcore",
        "hip-hop", "house", "indie", "instrumental", "intense", "jazz", "lofi", "lo-fi",
        "latin", "layered", "live", "lounge", "melodic", "metal", "minimal", "moody",
        "neo-soul", "orchestral", "piano", "pop", "powerful", "progressive", "psychedelic",
        "punk", "r&b", "rap", "reggae", "relaxing", "retro", "rock", "sad", "slow",
        "smooth", "soul", "soundtrack", "synth", "synthwave", "techno", "trap", "trance",
        "trippy", "uplifting", "vocal", "warm", "wave", "witch", "world", "808", "analog",
        "arpeggio", "ballad", "boom-bap", "choir", "cinematic", "club", "distorted",
        "dream-pop", "drums", "driving", "dynamic", "ethereal", "festive", "gritty",
        "groovy", "grunge", "harmonica", "heavy", "hypnotic", "industrial", "intimate",
        "mellow", "nostalgic", "organic", "percussion", "playful", "punchy", "quirky",
        "raw", "reverb", "rhythmic", "romantic", "saxophone", "shimmer", "sparse",
        "strings", "summer", "swing", "synth-pop", "tender", "textured", "tropical",
        "underground", "vibes", "vintage", "violin", "vocaloid", "waltz", "worship",
        "abstract", "aggressive", "airy", "anthemic", "avant-garde", "baroque", "bittersweet",
        "brooding", "catchy", "celtic", "chaotic", "cheerful", "creepy", "crisp", "cumbia",
        "cyberpunk", "daft", "delayed", "depressive", "dramatic", "drone", "dry", "dub",
        "echo", "eerie", "euphoric", "flamenco", "floating", "frantic", "french", "funky",
        "garage", "glitch", "gloomy", "glitchhop", "grime", "grit", "haunting", "hopeful",
        "humorous", "hyperpop", "icy", "idm", "improvised", "jangly", "jungle", "k-pop",
        "krautrock", "laid-back", "lush", "lyrical", "mad", "magical", "marching", "math",
        "meditative", "menacing", "mysterious", "nocturnal", "noisy", "nu-disco", "ominous",
        "opera", "optimistic", "outrun", "overdrive", "peaceful", "phonk", "polished",
        "post-punk", "post-rock", "pulsing", "ragtime", "rebellious", "resonant", "riot",
        "rustic", "salsa", "scary", "sci-fi", "shoegaze", "silky", "sinister", "ska",
        "slap", "sleek", "sloppy", "snappy", "soaring", "soft", "somber", "soothing",
        "spacey", "sparkling", "spooky", "staccato", "steady", "stoner", "stormy",
        "storytelling", "stripped", "subtle", "sultry", "sunny", "surfer", "suspense",
        "swagger", "swelling", "syncopated", "tense", "theatrical", "thumping", "tight",
        "tribal", "twangy", "unsettling", "urban", "urgent", "velvety", "volatile",
        "wonky", "woozy", "yacht", "yearning", "zen", "zydeco",
    )
)

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-']{1,30}")
_STOPWORDS = frozenset(
    "a an the and or but in on at to for of is it this that with from by as be are was were".split()
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokenize_creative_text(text: str) -> list[str]:
    if not text:
        return []
    low = text.lower()
    tokens = _TOKEN_RE.findall(low)
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2 and not t.isdigit()]


@dataclass
class StylePacks:
    """Suggested Suno style keyword strings derived from observed usage."""

    popular_pack: str = ""
    unused_pack: str = ""
    popular_terms: list[str] = field(default_factory=list)
    unused_terms: list[str] = field(default_factory=list)
    missing_from_seed: list[str] = field(default_factory=list)


class KeywordStyleAnalytics:
    """Persistent counters for tags/styles/prompt tokens + console reporting."""

    def __init__(self, path: str | Path = ".suno_keyword_analytics.json") -> None:
        self.path = Path(path)
        self._data: dict[str, Any] = self._load()

    def _empty(self) -> dict[str, Any]:
        return {
            "version": 2,
            "updated_at": _utc_now(),
            "keyword_counts": {},
            "tag_counts": {},
            "genre_counts": {},
            "style_counts": {},
            "prompt_token_counts": {},
            "seen_tokens": {},
            "songs_sampled": 0,
            "songs_skipped_no_traction": 0,
            "recent_songs": [],
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                raw.setdefault("version", 2)
                for k in (
                    "keyword_counts",
                    "tag_counts",
                    "genre_counts",
                    "style_counts",
                    "prompt_token_counts",
                    "seen_tokens",
                ):
                    raw.setdefault(k, {})
                raw.setdefault("recent_songs", [])
                return raw
        except Exception:
            pass
        return self._empty()

    def save(self) -> None:
        self._data["updated_at"] = _utc_now()
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_skipped_no_traction(self, n: int = 1) -> None:
        self._data["songs_skipped_no_traction"] = int(self._data.get("songs_skipped_no_traction", 0)) + n

    def _bump_map(self, key: str, term: str, amount: int = 1) -> None:
        bucket: dict = self._data.setdefault(key, {})
        norm = term.strip().lower()[:80]
        if not norm:
            return
        bucket[norm] = int(bucket.get(norm, 0)) + amount
        seen: dict = self._data.setdefault("seen_tokens", {})
        seen[norm] = int(seen.get(norm, 0)) + amount

    def ingest_song(
        self,
        *,
        url: str,
        title: str = "",
        prompt: str = "",
        lyrics: str = "",
        tags: list[str] | None = None,
        genres: list[str] | None = None,
        styles: list[str] | None = None,
        external_like_count: int = 0,
    ) -> None:
        tags = tags or []
        genres = genres or []
        styles = styles or []
        self._data["songs_sampled"] = int(self._data.get("songs_sampled", 0)) + 1

        for t in tags:
            self._bump_map("tag_counts", t)
        for g in genres:
            self._bump_map("genre_counts", g)
        for s in styles:
            self._bump_map("style_counts", s)

        blob = " ".join([title, prompt, lyrics, " ".join(tags), " ".join(genres), " ".join(styles)])
        for tok in tokenize_creative_text(blob):
            self._bump_map("keyword_counts", tok)
            self._bump_map("prompt_token_counts", tok)

        recent = self._data.setdefault("recent_songs", [])
        recent.append(
            {
                "url": url[:200],
                "title": title[:200],
                "prompt": prompt[:500],
                "lyrics": lyrics[:500],
                "tags": tags[:20],
                "genres": genres[:10],
                "styles": styles[:10],
                "external_like_count": external_like_count,
                "at": _utc_now(),
            }
        )
        self._data["recent_songs"] = recent[-400:]

    def _sorted_counter(self, key: str, limit: int = 30) -> list[tuple[str, int]]:
        bucket = self._data.get(key) or {}
        if not isinstance(bucket, dict):
            return []
        items = [(str(k), int(v)) for k, v in bucket.items() if v]
        items.sort(key=lambda x: (-x[1], x[0]))
        return items[:limit]

    def popular_keywords(self, limit: int = 25) -> list[tuple[str, int]]:
        merged: Counter[str] = Counter()
        for key in ("keyword_counts", "tag_counts", "genre_counts", "style_counts", "prompt_token_counts"):
            bucket = self._data.get(key) or {}
            if isinstance(bucket, dict):
                merged.update({str(k): int(v) for k, v in bucket.items()})
        return merged.most_common(limit)

    def unpopular_keywords(self, limit: int = 25) -> list[tuple[str, int]]:
        merged: Counter[str] = Counter()
        for key in ("keyword_counts", "tag_counts", "genre_counts", "style_counts", "prompt_token_counts"):
            bucket = self._data.get(key) or {}
            if isinstance(bucket, dict):
                merged.update({str(k): int(v) for k, v in bucket.items()})
        rare = [(k, c) for k, c in merged.items() if c == 1]
        rare.sort(key=lambda x: x[0])
        if len(rare) >= limit:
            return rare[:limit]
        low = sorted(merged.items(), key=lambda x: (x[1], x[0]))
        return low[:limit]

    def missing_english_seed_keywords(self, limit: int = 40) -> list[str]:
        """Seed vocabulary never observed in prompts/tags yet."""
        seen = set(self._data.get("seen_tokens") or {})
        missing = sorted(ENGLISH_SEED_KEYWORDS - seen)
        return missing[:limit]

    def novel_observed_keywords(self, limit: int = 30) -> list[tuple[str, int]]:
        """Tokens seen in the wild but not in our English seed list."""
        seen = self._data.get("seen_tokens") or {}
        if not isinstance(seen, dict):
            return []
        novel = [(k, int(v)) for k, v in seen.items() if k not in ENGLISH_SEED_KEYWORDS]
        novel.sort(key=lambda x: (-x[1], x[0]))
        return novel[:limit]

    def build_style_packs(self, *, popular_n: int = 12, unused_n: int = 12) -> StylePacks:
        popular_terms = [t for t, _ in self.popular_keywords(popular_n)]
        missing = self.missing_english_seed_keywords(unused_n)
        unused_terms = list(missing)
        if len(unused_terms) < unused_n:
            for t, _ in self.unpopular_keywords(unused_n - len(unused_terms)):
                if t not in unused_terms and t in ENGLISH_SEED_KEYWORDS:
                    unused_terms.append(t)
        unused_terms = unused_terms[:unused_n]
        popular_pack = ", ".join(popular_terms)
        unused_pack = ", ".join(unused_terms)
        return StylePacks(
            popular_pack=popular_pack,
            unused_pack=unused_pack,
            popular_terms=popular_terms,
            unused_terms=unused_terms,
            missing_from_seed=missing,
        )

    def format_console_report(self, *, top_n: int = 12, bottom_n: int = 12) -> str:
        packs = self.build_style_packs(popular_n=top_n, unused_n=bottom_n)
        pop = self.popular_keywords(top_n)
        unpop = self.unpopular_keywords(bottom_n)
        novel = self.novel_observed_keywords(10)
        missing = self.missing_english_seed_keywords(15)
        lines = [
            "--- KEYWORD / STYLE INTELLIGENCE ---",
            f"  songs sampled: {self._data.get('songs_sampled', 0)} | "
            f"skipped (no others' likes): {self._data.get('songs_skipped_no_traction', 0)}",
            f"  unique tokens seen: {len(self._data.get('seen_tokens') or {})} | "
            f"seed missing (never used): {len(ENGLISH_SEED_KEYWORDS - set(self._data.get('seen_tokens') or {}))}",
            "  TOP popular tags/keywords:",
        ]
        for term, cnt in pop[:top_n]:
            lines.append(f"    + {term}: {cnt}")
        lines.append("  Rare / unpopular (count=1 or low):")
        for term, cnt in unpop[:bottom_n]:
            lines.append(f"    - {term}: {cnt}")
        if novel:
            lines.append("  Novel (not in English seed list):")
            for term, cnt in novel[:8]:
                lines.append(f"    ? {term}: {cnt}")
        if missing:
            lines.append("  English seed keywords NOT yet seen on Suno:")
            lines.append(f"    {', '.join(missing[:15])}{'...' if len(missing) > 15 else ''}")
        lines.append("  STYLE PACK — often used:")
        lines.append(f"    {packs.popular_pack or '(collecting data)'}")
        lines.append("  STYLE PACK — try unused / missing:")
        lines.append(f"    {packs.unused_pack or '(collecting data)'}")
        lines.append("----------------------------------")
        return "\n".join(lines)
