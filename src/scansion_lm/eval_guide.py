"""Score a sheet against MasterofSFL's control rules."""

from __future__ import annotations

import re

from .corpus import THEMES, _lyrics, _style
from .extract import extract_song
from .infer import generate_sheet_from_lm, ready

NEEDED_TAGS = ["[Start]", "[Verse", "[Chorus", "[End]"]
ITALIAN = ["Largo", "Adagio", "Andante", "Moderato", "Allegretto", "Allegro", "Vivace", "Presto"]


def score_sheet(style: str, lyrics: str) -> dict:
    checks = []

    def add(name: str, ok: bool, note: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "note": note})

    add("start_end", "[Start]" in lyrics and "[End]" in lyrics, "Sheet is fenced with [Start]/[End]")
    add("verse", "[Verse" in lyrics, "Has a verse tag")
    add("chorus", any(t in lyrics for t in ("[Chorus", "[Hook", "[Drop")), "Has a chorus/hook tag")
    add("italian_tempo", any(t in lyrics or t in style for t in ITALIAN), "Italian tempo marking present")
    add("no_bpm_in_lyrics", not re.search(r"\[Tempo:\s*\d+\]", lyrics), "[Tempo: BPM] avoided")
    add("style_percent", "%" in (style or ""), "Genre percentage weighting in style")
    add("blank_line", "\n\n" in lyrics, "Breath/fill blank lines")
    add(
        "style_not_sung",
        "BPM" not in lyrics.split("[Verse", 1)[-1][:80] if "[Verse" in lyrics else True,
        "Style instructions not in sung lines",
    )
    ext = extract_song(lyrics)
    sung = [ln for ln in (ext.get("sung") or []) if ln and not ln.startswith("[")]
    add("sung_lines", len(sung) >= 6, f"{len(sung)} sung lines from the model")
    add("rhyme", bool(ext.get("rhyme_schema")), f"Rhyme schema {ext.get('rhyme_schema') or '—'}")
    add("sections", len(ext.get("sections") or []) >= 3, f"{len(ext.get('sections') or [])} sections")
    spam = bool(re.search(r"(\[Verse \d+\].*){4,}", lyrics.replace("\n", " ")))
    add("no_tag_spam", not spam, "No verse-tag loops")
    passed = sum(1 for c in checks if c["ok"])
    return {"passed": passed, "total": len(checks), "score": passed / len(checks), "checks": checks, "extract": ext}


def eval_model(n: int = 3) -> dict:
    """Score the causal LM (greedy decode), not the extract compiler."""
    if not ready():
        return {"ok": False, "error": "Model not trained", "average": 0, "reports": []}
    reports = []
    for i, (key, theme) in enumerate(THEMES.items()):
        if i >= n:
            break
        composer = {
            "title": theme["titles"][0],
            "idea": theme["ideas"][0],
            "pov": "first",
            "genres": [{"name": a, "weight": b} for a, b in theme["genre"]],
            "vocalGender": theme["vocal"][0],
            "vocalRange": theme["vocal"][1],
            "vocalDelivery": theme["vocal"][2],
            "tempo": theme["tempo"][0],
            "bpm": theme["tempo"][1],
            "timeSignature": theme["tempo"][2],
            "energy": theme["energy"],
            "structure": theme["form"],
            "rhyme": theme["rhyme"],
            "meterStagger": True,
            "extraBreaks": True,
            "callAndResponse": bool(theme.get("call")),
            "hitIds": [],
        }
        style_live = _style(theme, theme["titles"][0])
        gen = generate_sheet_from_lm(composer, style_live, theme["dna"])
        scored = score_sheet(gen["stylePrompt"], gen["lyrics"])
        reports.append(
            {
                "theme": key,
                "title": gen.get("title"),
                "engine": gen.get("engine", "local"),
                "preview": (gen.get("lyrics") or "")[:280],
                "sung": (gen.get("extract") or {}).get("sung") or [],
                **scored,
            }
        )
    avg = sum(r["score"] for r in reports) / max(len(reports), 1)
    return {"ok": True, "average": avg, "error": "", "reports": reports}


def gold_sheet_score() -> dict:
    theme = THEMES["desert"]
    lyrics = _lyrics(theme, "Mojave Bars", True, True, False)
    style = _style(theme, "Mojave Bars")
    return score_sheet(style, lyrics)
