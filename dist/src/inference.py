"""Reference / inference model for songwriting — learns from collected catalog data."""

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.keywords import ENGLISH_SEED_KEYWORDS, tokenize_creative_text
from src.catalog import SongCatalogStore, SongRecord

_STRUCTURE_RE = re.compile(
    r"^\s*\[?(verse|chorus|bridge|hook|intro|outro|pre-chorus|refrain)\s*\d*\]?\s*$",
    re.I | re.M,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StyleSuggestion:
    style_pack: str = ""
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.0
    based_on_songs: int = 0
    traction_tier: str = ""


@dataclass
class LyricTemplate:
    structure: list[str] = field(default_factory=list)
    sample_opening_lines: list[str] = field(default_factory=list)
    avg_line_count: int = 0
    rhyme_density: float = 0.0
    source_tier: str = ""


@dataclass
class SimilarSong:
    song_id: str
    title: str
    url: str
    score: float
    style_signature: str
    like_count: int


def resolve_inference_path(path: str | Path | None = None) -> Path:
    """Find the authoritative inference model file across root, dist, and parent folders."""
    if path:
        p = Path(path)
        if p.exists() and p.is_file() and p.stat().st_size > 100_000:
            return p
    candidates = [
        Path(path) if path else None,
        Path("dist/models/suno_song_inference_model.json"),
        Path("models/suno_song_inference_model.json"),
        Path("../models/suno_song_inference_model.json"),
        Path("../dist/models/suno_song_inference_model.json"),
        Path(__file__).resolve().parent.parent / "dist" / "models" / "suno_song_inference_model.json",
        Path(__file__).resolve().parent.parent / "models" / "suno_song_inference_model.json",
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
    return Path(path or "models/suno_song_inference_model.json")


class SongwritingReferenceModel:
    """
    Statistical reference model trained from the song catalog.
    Suggests styles, lyric structures, and similar songs without external ML deps.
    Retrain via `train_from_catalog()` as new data arrives.
    """

    def __init__(self, model_path: str | Path = "suno_song_inference_model.json") -> None:
        self.model_path = resolve_inference_path(model_path)
        self._state: dict[str, Any] = self._load()

    def _empty(self) -> dict[str, Any]:
        return {
            "version": 1,
            "trained_at": "",
            "songs_used": 0,
            "songs_with_lyrics": 0,
            "songs_with_structure": 0,
            "tag_traction": {},
            "style_cooccurrence": {},
            "structure_templates": {},
            "tier_tag_counts": {},
            "lyric_openings": {},
            "novel_keywords": {},
        }

    def _load(self) -> dict[str, Any]:
        if not self.model_path.exists():
            return self._empty()
        try:
            raw = json.loads(self.model_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                raw.setdefault("version", 1)
                return raw
        except Exception:
            pass
        return self._empty()

    def save(self) -> None:
        self._state["trained_at"] = _utc_now()
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(self._state, indent=2, ensure_ascii=False)
        self.model_path.write_text(serialized, encoding="utf-8")

        # Mirror save to sister models directories if present
        for candidate_dir in [
            Path(__file__).resolve().parent.parent / "models",
            Path(__file__).resolve().parent.parent / "dist" / "models",
        ]:
            if candidate_dir.exists() and candidate_dir != self.model_path.parent:
                mirror_path = candidate_dir / self.model_path.name
                try:
                    mirror_path.write_text(serialized, encoding="utf-8")
                except Exception:
                    pass

    def train_from_catalog(self, catalog: SongCatalogStore) -> int:
        from src.features import compute_lyric_stats

        records = sorted(
            catalog.all_records(),
            key=lambda r: (int(r.external_like_count or 0), int(r.play_count or 0)),
            reverse=True,
        )
        tag_traction: dict[str, list[int]] = defaultdict(list)
        style_co: Counter[str] = Counter()
        tier_tags: dict[str, Counter[str]] = defaultdict(Counter)
        structures: dict[str, list[dict]] = defaultdict(list)
        openings: dict[str, list[str]] = defaultdict(list)
        hooks: dict[str, list[str]] = defaultdict(list)
        novel: Counter[str] = Counter()

        for rec in records:
            tier = rec.derived_traction_tier or "none"
            all_tags = list(rec.tags) + list(rec.styles) + list(rec.genres)
            if rec.style_of_music:
                all_tags.extend(
                    t.strip() for t in re.split(r"[,;/|]+", rec.style_of_music) if t.strip()
                )
            tokens = tokenize_creative_text(rec.derived_style_signature or rec.style_of_music)
            for t in all_tags + tokens:
                norm = t.lower().strip()
                if not norm:
                    continue
                tag_traction[norm].append(rec.external_like_count)
                tier_tags[tier][norm] += 1
                if norm not in ENGLISH_SEED_KEYWORDS:
                    novel[norm] += 1
            pair_key = ",".join(sorted({t.lower() for t in all_tags if t})[:3])
            if pair_key:
                style_co[pair_key] += 1

            structure = list(rec.structure_tags or [])
            if not structure and rec.lyrics:
                structure = list(compute_lyric_stats(rec.lyrics).get("structure_tags") or [])
            if structure:
                key = "|".join(structure[:8])
                structures[key].append(
                    {
                        "line_count": rec.lyric_line_count,
                        "rhyme_density": rec.rhyme_density,
                        "tier": tier,
                        "likes": rec.external_like_count,
                    }
                )
            if rec.lyrics:
                lines = [
                    ln.strip()
                    for ln in rec.lyrics.splitlines()
                    if ln.strip()
                ]
                # Opening line
                for ln in lines:
                    if not _STRUCTURE_RE.match(ln) and self._usable_opening_line(ln):
                        if ln not in openings[tier] and len(openings[tier]) < 60:
                            openings[tier].append(ln[:140])
                        break

                # Hooks / chorus lines from viral and high tier tracks
                in_hook_block = False
                for ln in lines:
                    if re.search(r"\[(chorus|hook)", ln, re.I):
                        in_hook_block = True
                        continue
                    elif ln.startswith("["):
                        in_hook_block = False
                    elif in_hook_block and not ln.startswith("(") and len(ln) > 12:
                        if self._usable_opening_line(ln) and ln not in hooks[tier] and len(hooks[tier]) < 60:
                            hooks[tier].append(ln[:140])

        tag_scores = {}
        for tag, likes_list in tag_traction.items():
            if not likes_list:
                continue
            avg = sum(likes_list) / len(likes_list)
            tag_scores[tag] = {
                "avg_likes": round(avg, 2),
                "count": len(likes_list),
                "max_likes": max(likes_list),
            }

        self._state = {
            "version": 2,
            "trained_at": _utc_now(),
            "songs_used": len(records),
            "songs_with_lyrics": sum(1 for r in records if (r.lyrics or "").strip()),
            "songs_with_structure": sum(1 for k, v in structures.items() if v),
            "tag_traction": tag_scores,
            "style_cooccurrence": dict(style_co.most_common(200)),
            "structure_templates": {
                k: {
                    "count": len(v),
                    "avg_line_count": round(sum(x["line_count"] for x in v) / len(v), 1),
                    "avg_rhyme_density": round(sum(x["rhyme_density"] for x in v) / len(v), 3),
                    "best_tier": max(v, key=lambda x: x["likes"]).get("tier", ""),
                }
                for k, v in structures.items()
                if v
            },
            "tier_tag_counts": {tier: dict(cnt.most_common(40)) for tier, cnt in tier_tags.items()},
            "lyric_openings": {tier: samples[:50] for tier, samples in openings.items()},
            "lyric_hooks": {tier: samples[:50] for tier, samples in hooks.items()},
            "novel_keywords": dict(novel.most_common(80)),
        }
        return len(records)

    def get_top_viral_openings(self, genre: str = "", limit: int = 10) -> list[str]:
        """Return top learned opening lines from viral and high tier tracks in the catalog."""
        openings: list[str] = []
        for tier in ("viral", "high", "medium"):
            tier_lines = (self._state.get("lyric_openings") or {}).get(tier) or []
            for ln in tier_lines:
                if ln not in openings:
                    openings.append(ln)
        return openings[:limit]

    def get_top_hooks(self, genre: str = "", limit: int = 10) -> list[str]:
        """Return top learned chorus/hook lines from viral and high tier tracks in the catalog."""
        hooks: list[str] = []
        for tier in ("viral", "high", "medium"):
            tier_lines = (self._state.get("lyric_hooks") or {}).get(tier) or []
            for ln in tier_lines:
                if ln not in hooks:
                    hooks.append(ln)
        return hooks[:limit]

    def get_high_traction_tags(self, theme_keywords: list[str] | None = None, limit: int = 5) -> list[str]:
        """Return top performing tags matching prompt keywords or highest-performing globally."""
        tag_traction = self._state.get("tag_traction") or {}
        if not tag_traction:
            return []
        if theme_keywords:
            matched = [
                (tok, tag_traction[tok].get("avg_likes", 0))
                for tok in theme_keywords
                if tok in tag_traction
            ]
            matched.sort(key=lambda x: -x[1])
            if matched:
                return [m[0].upper() for m in matched[:limit]]
        ranked = sorted(
            tag_traction.items(),
            key=lambda x: (x[1].get("avg_likes", 0), x[1].get("count", 0)),
            reverse=True,
        )
        return [t.upper() for t, _ in ranked[:limit]]


    GENRE_ANCHORS = {
        "metal": [
            "industrial metal", "gothic metal", "dark", "aggressive", "heavy distortion",
            "crushing drop-D riffs", "double-kick blast beats", "raw", "cinematic", "melodic metalcore",
            "eerie dark synth textures", "raspy whisper to scream vocal",
        ],
        "rock": [
            "alternative rock", "overdriven guitars", "hard rock", "punchy live drums",
            "driving bassline", "grunge", "raw energy", "melodic rock", "radio master",
        ],
        "rap": [
            "drill rap", "trap", "sliding 808 glides", "hard punchy snare", "140 BPM",
            "aggressive cadence", "dark melodic synth", "fast syncopated delivery", "tight pocket",
        ],
        "synthwave": [
            "synthwave", "cyberpunk", "124 BPM", "analog arpeggiator", "gated reverb snare",
            "driving synth bassline", "retro-futuristic", "vocoder harmonies", "lush analog warmth",
        ],
        "pop": [
            "dance-pop", "catchy synth hooks", "bright radio master", "punchy electro kick",
            "sweet anthemic vocal belt", "wide stereo spread", "polished", "uplifting energy",
        ],
        "country": [
            "country pop", "fingerpicked acoustic guitar", "pedal steel", "warm resonant lead",
            "tight wooden percussion", "storytelling", "front porch warmth", "bittersweet",
        ],
        "rnb": [
            "contemporary r&b", "neo-soul", "warm rhodes piano", "breathy falsetto",
            "deep sub-bass", "laid-back groove", "gospel vocal harmonies", "intimate late-night vibe",
        ],
    }

    def suggest_style_pack(
        self,
        *,
        genre: str = "",
        theme: str = "",
        tier: str = "high",
        n: int = 12,
    ) -> StyleSuggestion:
        combined_req = (genre + " " + theme).lower()

        # Artist-specific overrides
        if any(w in combined_req for w in ("manson", "marylin", "marilyn")):
            artist_tags = [
                "industrial metal", "gothic shock rock", "90s industrial", "distorted mechanical bass synth",
                "crushing drop-D power chords", "eerie detuned synth pads", "raspy whisper to scream vocal",
                "cold aggressive industrial groove", "118 BPM", "dark", "polished radio master",
            ]
            return StyleSuggestion(
                style_pack=", ".join(artist_tags[:n]),
                tags=artist_tags[:n],
                confidence=0.95,
                based_on_songs=int(self._state.get("songs_used") or 0),
                traction_tier=tier,
            )
        elif any(w in combined_req for w in ("slipknot", "deathcore")):
            artist_tags = [
                "nu-metal", "downtuned drop-B riffs", "aggressive blast beats", "percussion barrage",
                "dual scream-clean vocals", "heavy groove", "raw aggressive", "double-kick thunder",
            ]
            return StyleSuggestion(
                style_pack=", ".join(artist_tags[:n]),
                tags=artist_tags[:n],
                confidence=0.95,
                based_on_songs=int(self._state.get("songs_used") or 0),
                traction_tier=tier,
            )
        elif any(w in combined_req for w in ("rammstein", "neue deutsche")):
            artist_tags = [
                "neue deutsche härte", "industrial metal", "marching 4-on-the-floor kick", "heavy power chords",
                "deep resonant baritone lead", "staccato guitar chug", "analog synth stabs", "120 BPM",
            ]
            return StyleSuggestion(
                style_pack=", ".join(artist_tags[:n]),
                tags=artist_tags[:n],
                confidence=0.95,
                based_on_songs=int(self._state.get("songs_used") or 0),
                traction_tier=tier,
            )

        # Genre detection
        matched_genre = ""
        for g_key in self.GENRE_ANCHORS:
            if g_key in combined_req:
                matched_genre = g_key
                break

        if matched_genre:
            anchors = list(self.GENRE_ANCHORS[matched_genre])
            tag_traction = self._state.get("tag_traction") or {}
            co = self._state.get("style_cooccurrence") or {}
            
            # Mine high-traction catalog tags matching genre
            mined: list[tuple[str, float]] = []
            for tag, st in tag_traction.items():
                t_clean = tag.strip().lower()
                if 3 <= len(t_clean) <= 30 and not any(p in t_clean for p in ("[", "]", "\n", "polished radio master", "keep core")):
                    if any(w in t_clean for w in [matched_genre, "dark", "heavy", "raw", "melodic", "driving", "aggressive"]):
                        score = st.get("avg_likes", 0) * 1.5 + st.get("count", 0) * 2.0
                        mined.append((t_clean, score))
            mined.sort(key=lambda x: -x[1])
            
            tags = list(anchors)
            for m_tag, _ in mined:
                if m_tag not in tags and len(tags) < n:
                    tags.append(m_tag)

            return StyleSuggestion(
                style_pack=", ".join(tags[:n]),
                tags=tags[:n],
                confidence=0.92,
                based_on_songs=int(self._state.get("songs_used") or 0),
                traction_tier=tier,
            )

        # Fallback to global traction tier tags
        tier_tags = (self._state.get("tier_tag_counts") or {}).get(tier) or {}
        tag_traction = self._state.get("tag_traction") or {}
        if not tier_tags:
            ranked = sorted(
                tag_traction.items(),
                key=lambda x: (x[1].get("avg_likes", 0), x[1].get("count", 0)),
                reverse=True,
            )
            tags = [t for t, _ in ranked[:n]]
        else:
            tags = list(tier_tags.keys())[:n]
        if len(tags) < n:
            missing = sorted(ENGLISH_SEED_KEYWORDS - set(tags))
            tags.extend(missing[: n - len(tags)])
        return StyleSuggestion(
            style_pack=", ".join(tags[:n]),
            tags=tags[:n],
            confidence=min(1.0, int(self._state.get("songs_used") or 0) / 50),
            based_on_songs=int(self._state.get("songs_used") or 0),
            traction_tier=tier,
        )

    def suggest_unused_style_pack(self, catalog: SongCatalogStore, n: int = 12) -> StyleSuggestion:
        seen = set()
        for rec in catalog.all_records():
            seen.update(rec.tags)
            seen.update(rec.styles)
            seen.update(tokenize_creative_text(rec.derived_style_signature))
        unused = sorted(ENGLISH_SEED_KEYWORDS - seen)
        novel = sorted(
            (self._state.get("novel_keywords") or {}).keys(),
            key=lambda k: -(self._state.get("novel_keywords") or {}).get(k, 0),
        )
        picks = unused[: max(4, n // 2)]
        for kw in novel:
            if len(picks) >= n:
                break
            if kw not in picks:
                picks.append(kw)
        return StyleSuggestion(
            style_pack=", ".join(picks[:n]),
            tags=picks[:n],
            confidence=0.5,
            based_on_songs=int(self._state.get("songs_used") or 0),
            traction_tier="explore",
        )

    def suggest_lyric_structure(self, *, tier: str = "high") -> LyricTemplate:
        templates = self._state.get("structure_templates") or {}
        if not templates:
            return LyricTemplate(
                structure=["verse", "chorus", "verse", "chorus", "bridge", "chorus"],
                sample_opening_lines=["First line sets the scene", "Hook lands on the chorus"],
                avg_line_count=24,
                rhyme_density=0.3,
                source_tier=tier,
            )
        ranked = sorted(
            templates.items(),
            key=lambda x: (x[1].get("best_tier") == tier, x[1].get("count", 0)),
            reverse=True,
        )
        key, info = ranked[0]
        structure = key.split("|") if key else ["verse", "chorus"]
        openings = (self._state.get("lyric_openings") or {}).get(tier) or []
        sample = random.sample(openings, min(3, len(openings))) if openings else []
        return LyricTemplate(
            structure=structure,
            sample_opening_lines=sample,
            avg_line_count=int(info.get("avg_line_count") or 0),
            rhyme_density=float(info.get("avg_rhyme_density") or 0),
            source_tier=tier,
        )

    def discover_similar(self, record: SongRecord, catalog: SongCatalogStore, limit: int = 8) -> list[SimilarSong]:
        target_tokens = set(tokenize_creative_text(record.derived_style_signature))
        target_tokens.update(t.lower() for t in record.tags)
        if not target_tokens:
            return []
        results: list[SimilarSong] = []
        for other in catalog.all_records():
            if other.song_id == record.song_id:
                continue
            other_tokens = set(tokenize_creative_text(other.derived_style_signature))
            other_tokens.update(t.lower() for t in other.tags)
            if not other_tokens:
                continue
            overlap = len(target_tokens & other_tokens)
            if overlap == 0:
                continue
            score = overlap / max(1, len(target_tokens | other_tokens))
            score += 0.1 * min(1.0, other.external_like_count / 100)
            results.append(
                SimilarSong(
                    song_id=other.song_id,
                    title=other.title,
                    url=other.url,
                    score=round(score, 3),
                    style_signature=other.derived_style_signature,
                    like_count=other.external_like_count,
                )
            )
        results.sort(key=lambda x: (-x.score, -x.like_count))
        return results[:limit]

    def _usable_opening_line(self, line: str) -> bool:
        t = (line or "").strip()
        if len(t) < 12 or len(t) > 160:
            return False
        if t.startswith("[") or t.startswith("("):
            return False
        words = [w for w in re.split(r"\s+", t) if w]
        if len(words) < 4:
            return False
        low = t.lower()
        if any(
            x in low
            for x in (
                "write 4 lines",
                "singing /",
                "smooth street",
                "style of music",
                "prompt:",
                "http://",
                "https://",
                "youtu.be",
                "youtube",
                "www.",
                "direitos",
                "reservados",
                "copyright",
                "all rights",
                "©",
                "lyrics by",
                "produced by",
                "once upon a time",
                "todos os direitos",
            )
        ):
            return False
        if re.fullmatch(r"[\w.\-]+", t):
            return False
        if re.search(r"\btold\b.+:", low):
            return False
        return True

    def _hook_phrase(self, theme_line: str, title: str = "") -> str:
        for candidate in (title, theme_line):
            c = (candidate or "").strip()
            if not c:
                continue
            c = re.sub(r"^(lyric about|song about|theme:)\s+", "", c, flags=re.I).strip()
            words = [w for w in re.split(r"\s+", c) if w]
            if not words:
                continue
            phrase = " ".join(words[:5])
            if self._usable_opening_line(phrase) or len(phrase.split()) <= 5:
                return phrase
        return "forever learning"

    def _compose_section_body(
        self,
        section: str,
        theme_line: str,
        *,
        index: int,
        openings: list[str],
        title: str = "",
    ) -> str:
        hook = self._hook_phrase(theme_line, title)
        usable = [o for o in openings if self._usable_opening_line(o)]
        sec = (section or "verse").lower().replace(" ", "-")
        if sec in ("chorus", "hook", "refrain"):
            return (
                f"{hook}\n"
                f"I never run out\n"
                f"{hook}\n"
                f"Keep on turning, forever learning"
            )
        if sec in ("pre-chorus", "prechorus"):
            return (
                f"If the world moves on\n"
                f"I move with it\n"
                f"If the night gets long\n"
                f"I get stronger for {hook}"
            )
        if sec == "bridge":
            return (
                f"And if you ask me what it feels like\n"
                f"It's a river with no last mile\n"
                f"It's a door that opens inward\n"
                f"Every time I smile for {hook}"
            )
        if sec in ("intro", "outro"):
            return f"(soft) {hook}\n(hold) forever learning"
        # verse
        if index == 0 and usable:
            base = usable[0]
            if "\n" not in base:
                base = (
                    f"{base}\n"
                    f"Yet the dawn keeps giving, day by day\n"
                    f"Every scar said you will stay\n"
                    f"So I laughed and let it play"
                )
            return base
        if usable and index < len(usable):
            return usable[index]
        verse_n = index + 1
        return (
            f"I woke up with the same old name\n"
            f"But the mirror learned a longer flame\n"
            f"Took a train past my second goodbye\n"
            f"Still chasing {hook} under verse {verse_n} sky"
        )

    def generate_prompt_seed(
        self,
        *,
        theme: str = "",
        tier: str = "high",
        include_structure: bool = True,
        title: str = "",
    ) -> dict[str, Any]:
        style = self.suggest_style_pack(tier=tier)
        lyric_tpl = self.suggest_lyric_structure(tier=tier) if include_structure else LyricTemplate()
        theme_tokens = tokenize_creative_text(theme)
        style_tags = list(style.tags)
        for t in theme_tokens:
            if t not in style_tags:
                style_tags.insert(0, t)
        style_tags = [
            t
            for t in style_tags
            if not re.fullmatch(r"v?\d+(\.\d+)?(-all|\+)?", t, re.I) and t.lower() != "studio"
        ]
        structure = lyric_tpl.structure or ["verse", "chorus", "verse", "chorus", "bridge", "chorus"]
        if len(structure) < 4:
            structure = ["verse", "pre-chorus", "chorus", "verse", "chorus", "bridge", "chorus"]
        openings = [o for o in (lyric_tpl.sample_opening_lines or []) if self._usable_opening_line(o)]
        theme_line = (theme or "midnight drive").strip()
        lyric_blocks: list[str] = []
        for i, section in enumerate(structure):
            label = section.replace("-", " ").title()
            body = self._compose_section_body(
                section, theme_line, index=i, openings=openings, title=title
            )
            lyric_blocks.append(f"[{label}]\n{body}")
        lyrics = "\n\n".join(lyric_blocks)
        song_title = (title or theme or "Untitled").strip()[:80]
        style_of_music = ", ".join(style_tags[:14])
        exclude = "low quality, muddy mix, off-key vocals, robotic cadence"
        paste_ready = (
            f"TITLE\n{song_title}\n\n"
            f"STYLE\n{style_of_music}\n\n"
            f"EXCLUDE\n{exclude}\n\n"
            f"LYRICS\n{lyrics}\n"
        )
        return {
            "title": song_title,
            "style_of_music": style_of_music,
            "exclude": exclude,
            "lyrics": lyrics,
            "suggested_structure": structure,
            "sample_opening_lines": openings,
            "theme": theme,
            "confidence": style.confidence,
            "based_on_songs": style.based_on_songs,
            "songs_with_lyrics": int(self._state.get("songs_with_lyrics") or 0),
            "negative_prompt": exclude,
            "paste_ready": paste_ready,
        }

    def write_prompt_file(
        self,
        path: str | Path,
        *,
        theme: str = "",
        tier: str = "high",
        title: str = "",
    ) -> Path:
        seed = self.generate_prompt_seed(theme=theme, tier=tier, title=title)
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        header = (
            f"# Generated from SongwritingReferenceModel\n"
            f"# trained_at={self._state.get('trained_at')}\n"
            f"# songs_used={self._state.get('songs_used')} "
            f"with_lyrics={self._state.get('songs_with_lyrics')} "
            f"structures={len(self._state.get('structure_templates') or {})}\n"
            f"# confidence={seed.get('confidence')}\n\n"
        )
        out.write_text(header + str(seed.get("paste_ready") or ""), encoding="utf-8")
        return out

    def format_report(self) -> str:
        n = int(self._state.get("songs_used") or 0)
        trained = self._state.get("trained_at") or "never"
        structures = len(self._state.get("structure_templates") or {})
        tags = len(self._state.get("tag_traction") or {})
        with_lyrics = int(self._state.get("songs_with_lyrics") or 0)
        lines = [
            "--- SONGWRITING INFERENCE MODEL ---",
            f"  model: {self.model_path}",
            f"  trained: {trained} | songs: {n} | with lyrics: {with_lyrics} | "
            f"tag scores: {tags} | structures: {structures}",
        ]
        style = self.suggest_style_pack()
        if style.style_pack:
            lines.append(f"  suggested style pack ({style.traction_tier}): {style.style_pack[:120]}")
        tpl = self.suggest_lyric_structure()
        if tpl.structure:
            lines.append(f"  suggested structure: {' -> '.join(tpl.structure[:8])}")
        lines.append("-----------------------------------")
        return "\n".join(lines)
