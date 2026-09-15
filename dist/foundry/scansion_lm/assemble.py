"""MasterofSFL sandwich encoder.

Places *already-written* sung lines into Custom Mode style + lyric metatags:
Italian tempo, genre %, [Start]/[End], blank-line breath, By-2s tags.
This module does not invent lyrics — the causal LM writes those.
"""

from __future__ import annotations

import re

from .corpus import THEMES, _pct_pair
from .extract import extract_song

SECTION_FORMS = {
    "standard": [
        ("[Verse 1]", "Verse", 4),
        ("[Pre-Chorus]", "Pre-Chorus", 2),
        ("[Chorus]", "Chorus", 4),
        ("[Verse 2]", "Verse", 4),
        ("[Bridge]", "Bridge", 2),
        ("[Chorus, Final, Harmonized]", "Chorus", 4),
    ],
    "anthem": [
        ("[Verse 1]", "Verse", 4),
        ("[Chorus]", "Chorus", 4),
        ("[Verse 2]", "Verse", 4),
        ("[Chorus]", "Chorus", 4),
        ("[Bridge]", "Bridge", 2),
        ("[Chorus, Final, Harmonized]", "Chorus", 4),
    ],
    "ballad": [
        ("[Verse 1]", "Verse", 4),
        ("[Verse 2]", "Verse", 4),
        ("[Chorus]", "Chorus", 4),
        ("[Bridge]", "Bridge", 2),
        ("[Chorus, Final, Harmonized]", "Chorus", 4),
    ],
    "rap": [
        ("[Verse 1]", "Verse", 6),
        ("[Hook]", "Chorus", 4),
        ("[Verse 2]", "Verse", 6),
        ("[Hook]", "Chorus", 4),
    ],
    "edm": [
        ("[Verse 1]", "Verse", 4),
        ("[Build]", "Pre-Chorus", 2),
        ("[Drop, Hook]", "Chorus", 4),
        ("[Verse 2]", "Verse", 4),
        ("[Drop, Hook]", "Chorus", 4),
    ],
    "country": [
        ("[Verse 1]", "Verse", 4),
        ("[Chorus]", "Chorus", 4),
        ("[Verse 2]", "Verse", 4),
        ("[Chorus]", "Chorus", 4),
        ("[Bridge]", "Bridge", 2),
        ("[Chorus, Final]", "Chorus", 4),
    ],
}


def invent_title(idea: str, fallback: str = "Untitled") -> str:
    stop = {
        "a", "an", "the", "and", "or", "but", "if", "to", "of", "in", "on", "at",
        "for", "from", "with", "by", "as", "is", "are", "was", "were", "be",
        "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her",
    }
    words = [w for w in re.findall(r"[A-Za-z']+", idea or "") if w.lower() not in stop]
    if len(words) >= 2:
        return f"{words[0].title()} {words[1].title()}"
    if words:
        return words[0].title()
    return fallback or "Untitled"


def closest_theme(composer: dict) -> str:
    names = " ".join(g.get("name", "") for g in (composer.get("genres") or [])).lower()
    structure = (composer.get("structure") or "").lower()
    mapping = [
        ("rap", ("hip-hop", "trap", "rap", "boom bap", "drill")),
        ("club", ("house", "edm", "dance", "techno", "hyperpop")),
        ("country", ("country", "americana")),
        ("soul", ("soul", "gospel", "r&b")),
        ("folk", ("folk", "singer")),
        ("desert", ("rock", "metal", "punk", "grunge")),
        ("night", ("synth", "pop", "disco")),
        ("quiet", ("ballad", "indie", "dream", "alt-pop")),
    ]
    for key, needles in mapping:
        if any(n in names or n in structure for n in needles):
            return key
    energy = int(composer.get("energy") or 50)
    if energy >= 75:
        return "desert"
    if energy <= 40:
        return "quiet"
    return "night"


def encode_style(composer: dict, live_style: str = "", dna: str = "") -> str:
    if live_style and len(live_style) > 40:
        return live_style[:900]
    key = closest_theme(composer)
    theme = THEMES[key]
    genres = composer.get("genres") or []
    if genres:
        gtxt = ", ".join(f"{g.get('name')} ({g.get('weight')}%)" for g in genres)
    else:
        gtxt = _pct_pair(theme["genre"])
    tempo = composer.get("tempo") or theme["tempo"][0]
    bpm = composer.get("bpm") or theme["tempo"][1]
    sig = composer.get("timeSignature") or theme["tempo"][2]
    delivery = composer.get("vocalDelivery") or theme["vocal"][2]
    gender = composer.get("vocalGender") or theme["vocal"][0]
    rng = composer.get("vocalRange") or theme["vocal"][1]
    extra = theme.get("style_extra", "studio mix")
    dna = dna or composer.get("dna") or theme.get("dna") or ""
    return (
        f"{gtxt}. {tempo} feel, {bpm} BPM, {sig}. {delivery}. {gender} lead"
        + (f", {rng}" if rng and rng != "Unspecified" else "")
        + f". {extra}. Distinct sections, studio production, no generic wash."
        + (f" {dna}" if dna else "")
    )[:900]


def form_spec(composer: dict) -> list[tuple[str, str, int]]:
    form = composer.get("structure") or "standard"
    spec = list(SECTION_FORMS.get(form, SECTION_FORMS["standard"]))
    if composer.get("meterStagger"):
        spec = [
            (tag.replace("[Verse 2]", "[Verse 2: Staggered meter, alternate feet]"), kind, n)
            for tag, kind, n in spec
        ]
    key = closest_theme(composer)
    theme = THEMES[key]
    tags = theme.get("tags") or ()
    if tags and spec:
        flavor = tags[0]
        if flavor.startswith("[Verse") and spec[0][0].startswith("[Verse 1]"):
            spec[0] = (flavor, spec[0][1], spec[0][2])
        chorus_i = next((i for i, s in enumerate(spec) if s[1] == "Chorus"), None)
        if chorus_i is not None and len(tags) > 1 and "Chorus" in tags[1]:
            spec[chorus_i] = (tags[1], spec[chorus_i][1], spec[chorus_i][2])
    return spec


def wrap_lyrics(
    composer: dict,
    blocks: list[tuple[str, list[str]]],
    live_style: str = "",
    dna: str = "",
) -> tuple[str, str, str]:
    """Encode LM lines into a paste-ready sandwich. Returns (style, lyrics, title)."""
    key = closest_theme(composer)
    theme = THEMES[key]
    title = (composer.get("title") or "").strip() or invent_title(composer.get("idea") or "", theme["titles"][0])
    tempo = composer.get("tempo") or theme["tempo"][0]
    intro = theme["style_extra"].split(",")[0]
    extra = bool(composer.get("extraBreaks", True))
    air = int(composer.get("energy") or 50) <= 38
    call = bool(composer.get("callAndResponse"))
    style = encode_style(composer, live_style, dna)

    parts: list[str] = [
        "[Start]",
        "[Silence 3s]" if air else "[Intro hit]",
        f"[Tempo: {tempo}]",
        f"[Intro: {intro}]",
    ]
    for tag, lines in blocks:
        sung = [ln.strip() for ln in lines if ln and ln.strip()]
        if call and any(k in tag for k in ("Chorus", "Hook", "Drop")):
            sung = [ln if "(say it back)" in ln.lower() else f"{ln} (say it back)" for ln in sung]
        if extra:
            parts.append("")
        parts.append(tag)
        parts.extend(sung)
    parts.append("[End]")
    lyrics = "\n".join(parts)
    return style[:900], lyrics[:2600], title


def pack_generation(
    composer: dict,
    style: str,
    lyrics: str,
    title: str,
    raw: str = "",
    why: str = "",
) -> dict:
    ext = extract_song(lyrics, title=title, source="infer")
    key = closest_theme(composer)
    theme = THEMES[key]
    bpm = int(composer.get("bpm") or theme["tempo"][1])
    energy = int(composer.get("energy") or theme["energy"])
    hit_ids = composer.get("hitIds") or []
    return {
        "title": title,
        "stylePrompt": style[:1000],
        "lyrics": lyrics[:5000],
        "sliders": {
            "weirdness": 38 if hit_ids else 52,
            "styleInfluence": 82 if hit_ids else 70,
            "audioInfluence": 18,
        },
        "tempoMarking": composer.get("tempo") or theme["tempo"][0],
        "bpm": bpm,
        "timeSignature": composer.get("timeSignature") or theme["tempo"][2],
        "meterMap": [
            {"section": m["section"], "lines": m.get("feet") or [m.get("dominant_foot", "free")]}
            for m in ext.get("meter_map", [])
        ],
        "rhymeSchema": ext.get("rhyme_schema") or composer.get("rhyme") or "",
        "vocalBrief": f"{composer.get('vocalGender')} {composer.get('vocalRange')} / {composer.get('vocalDelivery')}",
        "whyItWorks": why
        or (
            "Scansion-LM (distilgpt2 fine-tuned on original lyric extracts) writes every sung line. "
            "The metatag sandwich, Italian tempo, and genre percentages are encoded from the MasterofSFL "
            "guide so the sheet pastes into Suno Custom Mode."
        ),
        "sunoNotes": [
            "Paste STYLE into Suno's style field and LYRICS into Custom Mode lyrics.",
            "Italian tempo is in the metatags; BPM lives in style.",
            "Blank lines are breaths. If a line glitches, run Smooth meter.",
            "Clip the strongest chorus + verse 1 for a persona.",
        ],
        "personaClip": "Clip chorus + first verse after a clean take.",
        "hitDnaUsed": hit_ids,
        "engine": "local",
        "energyGuess": energy,
        "theme": key,
        "raw": (raw or "")[:4000],
        "extract": {
            "sections": ext.get("sections"),
            "rhyme_schema": ext.get("rhyme_schema"),
            "energy": ext.get("energy"),
            "masculine_endings": ext.get("masculine_endings"),
            "feminine_endings": ext.get("feminine_endings"),
            "sung": ext.get("sung"),
        },
    }
