"""Compute derived songwriting features from raw Suno song metadata."""

from __future__ import annotations

import re
from typing import Any

from src.keywords import ENGLISH_SEED_KEYWORDS, tokenize_creative_text

_SECTION_MARKERS = re.compile(
    r"^\s*\[?(verse|chorus|bridge|hook|intro|outro|pre-chorus|refrain|break|drop|"
    r"spoken|rap|interlude|solo|instrumental)\s*\d*\]?\s*$",
    re.I | re.M,
)
_SECTION_INLINE = re.compile(
    r"\[(verse|chorus|bridge|hook|intro|outro|pre-chorus|refrain|break|drop|"
    r"spoken|rap|interlude|solo|instrumental)\s*\d*\]",
    re.I,
)
_RHYME_END_RE = re.compile(r"[a-z]{3,}$")
_INSTRUMENTAL_HINTS = frozenset(
    {"instrumental", "no vocals", "no lyrics", "beat only", "type beat", "inst"}
)


def _clean_text(value: Any, limit: int = 8000) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text[:limit] if text else ""


def _split_listish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if re.search(r"[,;|/]", text):
            parts = re.split(r"[,;|/]+", text)
            return [p.strip() for p in parts if p.strip()]
        if " " in text and len(text) > 24:
            return tokenize_creative_text(text)[:20]
        return [text]
    return []


def normalize_tags(*sources: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for src in sources:
        for item in _split_listish(src):
            norm = item.lower()[:80]
            if norm and norm not in seen:
                seen.add(norm)
                out.append(norm)
    return out[:40]


def unwrap_clip_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten Suno song_schema payloads.
    Public studio-api stores lyrics in metadata.prompt and style tags in metadata.tags.
    """
    if not isinstance(raw, dict):
        return {}
    meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    out = dict(raw)
    if not _clean_text(out.get("lyrics")):
        out["lyrics"] = meta.get("prompt") or meta.get("lyrics") or out.get("lyrics") or ""
    if not _clean_text(out.get("style_of_music") or out.get("style")):
        out["style_of_music"] = (
            meta.get("tags")
            or meta.get("gpt_description_prompt")
            or out.get("style_of_music")
            or out.get("style")
            or ""
        )
    if not _clean_text(out.get("prompt")) and meta.get("gpt_description_prompt"):
        out["prompt"] = meta.get("gpt_description_prompt")
    if not _clean_text(out.get("negative_prompt")):
        out["negative_prompt"] = meta.get("negative_tags") or meta.get("negative_prompt") or ""
    if out.get("duration") is None and meta.get("duration") is not None:
        out["duration"] = meta.get("duration")
    if out.get("is_instrumental") is None and meta.get("make_instrumental") is not None:
        out["is_instrumental"] = bool(meta.get("make_instrumental"))
    if not out.get("artist_id") and isinstance(out.get("handle"), str):
        out["artist_id"] = out["handle"]
    if not out.get("artist_name") and isinstance(out.get("display_name"), str):
        out["artist_name"] = out["display_name"]
    if meta:
        out["_metadata"] = meta
    return out


def separate_creative_fields(raw: dict[str, Any]) -> dict[str, str]:
    """Split prompt, lyrics, style, and description from heterogeneous Suno payloads."""
    raw = unwrap_clip_metadata(raw if isinstance(raw, dict) else {})
    prompt = _clean_text(raw.get("prompt"))
    lyrics = _clean_text(raw.get("lyrics"))
    gpt_description = _clean_text(raw.get("gpt_description"))
    description = _clean_text(raw.get("description"))
    style_of_music = _clean_text(
        raw.get("style_of_music") or raw.get("style") or raw.get("style_prompt")
    )
    negative_prompt = _clean_text(raw.get("negative_prompt") or raw.get("negative_tags"))

    if not lyrics and prompt and _looks_like_lyrics(prompt):
        lyrics, prompt = prompt, ""
    if not lyrics and gpt_description and _looks_like_lyrics(gpt_description):
        lyrics = gpt_description
    if not style_of_music and prompt and not _looks_like_lyrics(prompt) and len(prompt) < 400:
        style_of_music = prompt
        prompt = ""

    title = _clean_text(raw.get("title") or raw.get("name"))
    combined = " ".join(
        x for x in (title, style_of_music, prompt, lyrics, gpt_description, description) if x
    )
    return {
        "title": title,
        "prompt": prompt,
        "lyrics": lyrics,
        "gpt_description": gpt_description,
        "description": description,
        "style_of_music": style_of_music,
        "negative_prompt": negative_prompt,
        "combined_creative_text": combined[:6000],
    }


def _looks_like_lyrics(text: str) -> bool:
    if not text or len(text) < 40:
        return False
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 3:
        return False
    section_hits = sum(1 for ln in lines if _SECTION_MARKERS.match(ln))
    long_lines = sum(1 for ln in lines if len(ln) > 20)
    return section_hits >= 1 or (len(lines) >= 6 and long_lines >= 3)


def compute_lyric_stats(lyrics: str) -> dict[str, Any]:
    text = (lyrics or "").strip()
    if not text:
        return {
            "lyric_line_count": 0,
            "lyric_word_count": 0,
            "lyric_avg_line_length": 0.0,
            "lyric_line_length_stdev": 0.0,
            "lyric_unique_word_ratio": 0.0,
            "lyric_repeated_line_ratio": 0.0,
            "lyric_section_count": 0,
            "structure_tags": [],
            "rhyme_density": 0.0,
        }
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    words = re.findall(r"[a-zA-Z']+", text.lower())
    structure: list[str] = []
    for ln in lines:
        m = _SECTION_MARKERS.match(ln)
        if m:
            tag = m.group(1).lower()
            if not structure or structure[-1] != tag:
                structure.append(tag)
            continue
        for m in _SECTION_INLINE.finditer(ln):
            tag = m.group(1).lower()
            if not structure or structure[-1] != tag:
                structure.append(tag)
    if not structure:
        for m in _SECTION_INLINE.finditer(text):
            tag = m.group(1).lower()
            if not structure or structure[-1] != tag:
                structure.append(tag)
    rhyme_endings: list[str] = []
    for ln in lines:
        if _SECTION_MARKERS.match(ln):
            continue
        tokens = re.findall(r"[a-zA-Z']+", ln.lower())
        if tokens:
            rhyme_endings.append(tokens[-1])
    rhyme_pairs = 0
    for i, a in enumerate(rhyme_endings):
        for b in rhyme_endings[i + 1 :]:
            if a == b and len(a) >= 4:
                rhyme_pairs += 1
                break
    rhyme_density = round(rhyme_pairs / max(1, len(rhyme_endings)), 3)
    avg_len = round(sum(len(ln) for ln in lines) / max(1, len(lines)), 1)
    line_lengths = [len(ln) for ln in lines]
    mean_len = sum(line_lengths) / max(1, len(line_lengths))
    line_variance = sum((n - mean_len) ** 2 for n in line_lengths) / max(1, len(line_lengths))
    stdev = round(line_variance ** 0.5, 1)
    unique_word_ratio = round(len(set(words)) / max(1, len(words)), 3)
    repeated_line_ratio = round(1 - (len(set(lines)) / max(1, len(lines))), 3)
    return {
        "lyric_line_count": len(lines),
        "lyric_word_count": len(words),
        "lyric_avg_line_length": avg_len,
        "lyric_line_length_stdev": stdev,
        "lyric_unique_word_ratio": unique_word_ratio,
        "lyric_repeated_line_ratio": repeated_line_ratio,
        "lyric_section_count": len(structure),
        "structure_tags": structure[:16],
        "rhyme_density": rhyme_density,
    }


def classify_authorship(
    *,
    title: str = "",
    prompt: str = "",
    lyrics: str = "",
    structure_tags: list[str] | None = None,
    line_count: int | None = None,
    unique_word_ratio: float | None = None,
    repeated_line_ratio: float | None = None,
    line_length_stdev: float | None = None,
) -> dict[str, Any]:
    structure_tags = structure_tags or []
    text = (lyrics or "").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    words = re.findall(r"[a-zA-Z']+", text.lower())
    line_count = line_count if line_count is not None else len(lines)
    unique_word_ratio = unique_word_ratio if unique_word_ratio is not None else (
        round(len(set(words)) / max(1, len(words)), 3) if words else 0.0
    )
    repeated_line_ratio = repeated_line_ratio if repeated_line_ratio is not None else (
        round(1 - (len(set(lines)) / max(1, len(lines))), 3) if lines else 0.0
    )
    line_length_stdev = line_length_stdev if line_length_stdev is not None else (
        round((sum((len(ln) - (sum(len(ln) for ln in lines) / max(1, len(lines)))) ** 2 for ln in lines) / max(1, len(lines))) ** 0.5, 1)
        if lines else 0.0
    )

    ai_score = 0.5
    signals: list[str] = []

    if text:
        if line_count >= 16:
            ai_score += 0.08
            signals.append("long_form_structure")
        if 3 <= line_count <= 8 and not structure_tags:
            ai_score -= 0.05
            signals.append("short_unstructured_form")
        if len(structure_tags) >= 3:
            ai_score += 0.10
            signals.append("section_markers")
        if repeated_line_ratio >= 0.12:
            ai_score += 0.14
            signals.append("repeated_lines")
        if repeated_line_ratio <= 0.02 and line_count <= 8:
            ai_score -= 0.04
            signals.append("nonrepetitive_short_form")
        if unique_word_ratio <= 0.34:
            ai_score += 0.14
            signals.append("low_lexical_diversity")
        if unique_word_ratio >= 0.62:
            ai_score -= 0.10
            signals.append("high_lexical_variety")
        if line_length_stdev <= 6.0 and line_count >= 8:
            ai_score += 0.08
            signals.append("regular_line_lengths")
        if line_length_stdev >= 8.0 and line_count >= 4:
            ai_score -= 0.08
            signals.append("irregular_line_lengths")
        if len(words) >= 120 and len(set(words)) >= 55:
            ai_score += 0.04
            signals.append("dense_but_generic")
        if any(tag.lower() in {"verse", "chorus", "hook", "bridge", "intro", "outro"} for tag in structure_tags):
            ai_score += 0.06
            signals.append("templated_sections")
        if any(tok in text.lower() for tok in ("ai", "generated", "prompt", "suno", "model", "style of music")):
            ai_score += 0.08
            signals.append("meta_generation_terms")
        if any(tok in text.lower() for tok in ("i was", "my mom", "my dad", "my hood", "my block", "last night", "yesterday", "this morning")):
            ai_score -= 0.06
            signals.append("personal_time_markers")
        if any(tok in text.lower() for tok in ("uh", "um", "nah", "yo", "lemme", "ain't", "gonna")):
            ai_score -= 0.04
            signals.append("casual_speech_markers")

    if title and len(title.split()) >= 4:
        ai_score += 0.02
        signals.append("formulaic_title")
    if prompt and len(prompt) >= 40 and len(prompt) < 500:
        ai_score += 0.03
        signals.append("prompt_like_metadata")

    ai_score = max(0.0, min(1.0, round(ai_score, 3)))
    if ai_score >= 0.65:
        label = "likely_ai"
    elif ai_score <= 0.35:
        label = "likely_handwritten"
    else:
        label = "mixed_or_unclear"
    return {
        "authorship_label": label,
        "authorship_ai_score": ai_score,
        "authorship_handwritten_score": round(1.0 - ai_score, 3),
        "authorship_signals": signals[:16],
    }


def compute_style_signature(
    *,
    tags: list[str],
    genres: list[str],
    styles: list[str],
    style_of_music: str = "",
    prompt: str = "",
) -> str:
    parts = normalize_tags(tags, genres, styles)
    if style_of_music:
        parts.extend(tokenize_creative_text(style_of_music))
    if prompt and len(prompt) < 300:
        parts.extend(tokenize_creative_text(prompt))
    seen: set[str] = set()
    ordered: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ", ".join(ordered[:20])


def compute_traction_tier(like_count: int) -> str:
    if like_count >= 500:
        return "viral"
    if like_count >= 100:
        return "high"
    if like_count >= 20:
        return "medium"
    if like_count >= 1:
        return "low"
    return "none"


def detect_instrumental(
    *,
    lyrics: str,
    tags: list[str],
    styles: list[str],
    explicit: bool | None = None,
) -> bool | None:
    if explicit is not None:
        return explicit
    blob = " ".join([lyrics or "", " ".join(tags), " ".join(styles)]).lower()
    if any(h in blob for h in _INSTRUMENTAL_HINTS):
        return True
    if lyrics and len(lyrics.strip()) > 30:
        return False
    return None


def compute_seed_alignment(tags: list[str], styles: list[str], prompt: str) -> dict[str, Any]:
    tokens = set(tokenize_creative_text(" ".join(tags + styles + [prompt])))
    matched = sorted(tokens & ENGLISH_SEED_KEYWORDS)
    novel = sorted(tokens - ENGLISH_SEED_KEYWORDS)[:30]
    return {
        "seed_keyword_hits": matched[:25],
        "novel_keywords": novel[:25],
        "seed_coverage_ratio": round(len(matched) / max(1, len(tokens)), 3),
    }


def derive_song_features(record: dict[str, Any]) -> dict[str, Any]:
    """Return derived fields to merge into a catalog record."""
    creative = separate_creative_fields(record)
    tags = normalize_tags(
        record.get("tags"),
        record.get("genres"),
        record.get("styles"),
        record.get("tag_list"),
        record.get("style_tags"),
        creative["style_of_music"],
    )
    genres = normalize_tags(record.get("genres"))
    styles = normalize_tags(record.get("styles"))
    lyric_stats = compute_lyric_stats(creative["lyrics"])
    likes = int(record.get("external_like_count") or record.get("like_count") or 0)
    prompt_tokens = tokenize_creative_text(creative["combined_creative_text"])[:50]
    seed_info = compute_seed_alignment(tags, styles, creative["style_of_music"] or creative["prompt"])
    instrumental = detect_instrumental(
        lyrics=creative["lyrics"],
        tags=tags,
        styles=styles,
        explicit=record.get("is_instrumental"),
    )
    authorship = classify_authorship(
        title=creative["title"] or str(record.get("title") or ""),
        prompt=creative["prompt"],
        lyrics=creative["lyrics"],
        structure_tags=lyric_stats.get("structure_tags") or [],
        line_count=lyric_stats.get("lyric_line_count"),
        unique_word_ratio=lyric_stats.get("lyric_unique_word_ratio"),
        repeated_line_ratio=lyric_stats.get("lyric_repeated_line_ratio"),
        line_length_stdev=lyric_stats.get("lyric_line_length_stdev"),
    )
    return {
        **creative,
        "tags": tags,
        "genres": genres,
        "styles": styles,
        "derived_style_signature": compute_style_signature(
            tags=tags,
            genres=genres,
            styles=styles,
            style_of_music=creative["style_of_music"],
            prompt=creative["prompt"],
        ),
        "derived_traction_tier": compute_traction_tier(likes),
        "derived_prompt_tokens": prompt_tokens,
        "derived_is_instrumental": instrumental,
        **lyric_stats,
        **seed_info,
        **authorship,
    }


def slim_raw_feed_json(obj: dict[str, Any]) -> dict[str, Any]:
    """Keep a compact subset of feed API payload for dataset lineage."""
    keys = (
        "id",
        "title",
        "name",
        "prompt",
        "lyrics",
        "gpt_description",
        "description",
        "tags",
        "tag_list",
        "styles",
        "genres",
        "style_tags",
        "audio_url",
        "image_url",
        "video_url",
        "duration",
        "created_at",
        "status",
        "entity_type",
        "model_name",
        "major_model_version",
        "type",
        "is_instrumental",
        "like_count",
        "upvote_count",
        "play_count",
        "comment_count",
        "handle",
        "display_name",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if k in obj and obj[k] not in (None, "", [], {}):
            out[k] = obj[k]
    meta = obj.get("metadata")
    if isinstance(meta, dict):
        slim_meta = {
            k: meta[k]
            for k in (
                "prompt",
                "lyrics",
                "tags",
                "gpt_description_prompt",
                "negative_tags",
                "duration",
                "make_instrumental",
                "type",
                "task",
            )
            if meta.get(k) not in (None, "", [], {})
        }
        if slim_meta:
            out["metadata"] = slim_meta
    user = obj.get("user") or obj.get("artist") or obj.get("creator")
    if isinstance(user, dict):
        out["user_handle"] = user.get("handle") or user.get("username") or user.get("display_name")
        out["user_id"] = user.get("id")
    return out
