"""Build a massive training corpus for causal language modeling and reference intelligence from 7,000+ Suno songs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from src.catalog import SongCatalogStore

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BOS_BRIEF = "<|brief|>"
BOS_SHEET = "<|sheet|>"
EOS = "<|end|>"


def parse_song_sections(lyrics: str) -> list[tuple[str, list[str]]]:
    """Segment raw lyrics into named section blocks ([Verse], [Chorus], etc.)."""
    if not lyrics or not lyrics.strip():
        return []

    sections: list[tuple[str, list[str]]] = []
    curr_name = "Verse"
    curr_lines: list[str] = []

    for line in lyrics.splitlines():
        line_s = line.strip()
        if not line_s:
            continue
        m = re.match(r"^\[([a-zA-Z0-9\s,\-_]+)\]$", line_s)
        if m:
            if curr_lines:
                sections.append((curr_name, list(curr_lines)))
                curr_lines.clear()
            raw_tag = m.group(1).strip()
            tag_low = raw_tag.lower()
            if "verse" in tag_low:
                curr_name = "Verse"
            elif "chorus" in tag_low or "hook" in tag_low:
                curr_name = "Chorus"
            elif "pre" in tag_low:
                curr_name = "Pre-Chorus"
            elif "bridge" in tag_low:
                curr_name = "Bridge"
            elif "intro" in tag_low:
                curr_name = "Intro"
            elif "outro" in tag_low or "fade" in tag_low:
                curr_name = "Outro"
            elif "drop" in tag_low or "build" in tag_low or "solo" in tag_low:
                curr_name = "Breakdown"
            else:
                curr_name = raw_tag.title()
        else:
            curr_lines.append(line_s)

    if curr_lines:
        sections.append((curr_name, list(curr_lines)))

    return sections


def build_massive_corpus(
    catalog_path: str | Path = "dist/models/suno_song_catalog.json",
    out_jsonl: str | Path = "dist/corpus/suno_lyrics_corpus.jsonl",
    foundry_corpus_jsonl: str | Path = "C:/Users/Dean/Downloads/sadLUMBWP5nexOWh-grok-workspace/foundry/data/corpus.jsonl",
) -> dict[str, Any]:
    """Extract full scansion sheets, section continuations, and metatags from all 7k+ songs."""
    catalog_path = Path(catalog_path)
    out_jsonl = Path(out_jsonl)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  MASSIVE SUNO 7,000+ SONG CORPUS BUILDER")
    print("=" * 65)
    print(f"Source Catalog:    {catalog_path}")
    print(f"Output Corpus:     {out_jsonl}")
    print("-" * 65)

    catalog = SongCatalogStore(catalog_path)
    records = catalog.all_records()
    print(f"[*] Loaded {len(records):,} records from catalog...")

    corpus_records: list[dict[str, Any]] = []
    seen_texts: set[str] = set()

    section_counts: dict[str, int] = {}
    genre_counts: dict[str, int] = {}
    total_words = 0
    unique_words: set[str] = set()

    for song in records:
        lyrics = (song.lyrics or "").strip()
        if not lyrics or len(lyrics) < 40:
            continue

        title = (song.title or "Suno Track").strip()
        style = (song.style_of_music or song.prompt or ", ".join(song.tags[:6]) or "Pop").strip()
        style_clean = re.sub(r"\s+", " ", style)[:140]

        # 1. Full song sheet format: <|brief|>\nTitle: ...\n<|sheet|>\n...<|end|>
        sheet_prompt = f"{BOS_BRIEF}\nTitle: {title}\nStyle: {style_clean}\n{BOS_SHEET}\n"
        sheet_full = f"{sheet_prompt}{lyrics}\n{EOS}"
        if sheet_full not in seen_texts:
            seen_texts.add(sheet_full)
            corpus_records.append({
                "prompt": sheet_prompt,
                "text": sheet_full,
                "title": title,
                "style": style_clean,
                "kind": "full_sheet",
                "char_len": len(sheet_full),
            })
            words = [w.lower() for w in re.findall(r"\b[a-zA-Z']+\b", sheet_full)]
            total_words += len(words)
            unique_words.update(words)

        # 2. Section-by-section scansion continuations:
        sections = parse_song_sections(lyrics)
        for sec_name, lines in sections:
            if not lines:
                continue
            sec_text = "\n".join(lines[:14])
            sec_prompt = f"Title: {title}\nIdea: {style_clean}\n{sec_name}:\n"
            sec_full = f"{sec_prompt}{sec_text}"

            if sec_full not in seen_texts:
                seen_texts.add(sec_full)
                corpus_records.append({
                    "prompt": sec_prompt,
                    "text": sec_full,
                    "title": title,
                    "style": style_clean,
                    "section": sec_name,
                    "kind": "section_continuation",
                    "lines_count": len(lines),
                    "char_len": len(sec_full),
                })
                section_counts[sec_name] = section_counts.get(sec_name, 0) + 1
                words = [w.lower() for w in re.findall(r"\b[a-zA-Z']+\b", sec_full)]
                total_words += len(words)
                unique_words.update(words)

        # Track tags
        for t in song.tags:
            t_low = t.lower()
            genre_counts[t_low] = genre_counts.get(t_low, 0) + 1

    # Write output jsonl
    print(f"[*] Writing {len(corpus_records):,} compiled records to {out_jsonl}...")
    with open(out_jsonl, "w", encoding="utf-8") as fh:
        for r in corpus_records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Also sync into foundry data directory if available
    foundry_p = Path(foundry_corpus_jsonl)
    if foundry_p.parent.exists():
        try:
            print(f"[*] Syncing massive corpus to foundry: {foundry_p}...")
            foundry_p.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in corpus_records),
                encoding="utf-8",
            )
            user_extracts = foundry_p.parent / "user_extracts.jsonl"
            user_extracts.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in corpus_records[:2000]),
                encoding="utf-8",
            )
            print(f"[+] Synced {len(corpus_records):,} records to foundry directory!")
        except Exception as e:
            print(f"[!] Note: could not sync to foundry path: {e}")

    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_sections = sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    report = f"""
======================================================================
  CORPUS INTELLIGENCE & SCALE REPORT
======================================================================
  Total Compiled Training Records:   {len(corpus_records):,}
  Total Running Words:               {total_words:,}
  Unique Lyrical Vocabulary Size:    {len(unique_words):,} words
  Average Words per Song Sheet:      {round(total_words / max(1, len(corpus_records)), 1)}
  Primary Lyrical Sections Extracted:
{chr(10).join(f'    • {k:<15} : {v:,} blocks' for k, v in top_sections)}

  Top Musical Genres & Tag Clusters in Corpus:
{chr(10).join(f'    • {k:<15} : {v:,} tracks' for k, v in top_genres)}
======================================================================
"""
    print(report)

    meta_path = out_jsonl.with_suffix(".stats.json")
    meta_path.write_text(
        json.dumps({
            "total_records": len(corpus_records),
            "total_words": total_words,
            "unique_vocabulary": len(unique_words),
            "top_sections": dict(top_sections),
            "top_genres": dict(top_genres),
        }, indent=2),
        encoding="utf-8",
    )

    return {
        "records": len(corpus_records),
        "total_words": total_words,
        "unique_words": len(unique_words),
        "path": str(out_jsonl),
    }


if __name__ == "__main__":
    build_massive_corpus()
