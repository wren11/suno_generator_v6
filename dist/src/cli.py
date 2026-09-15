"""CLI entry point for Suno Generator (training, generation, export, stats, and REPL)."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from src.catalog import SongCatalogStore
from src.inference import SongwritingReferenceModel
from src.repl import SunoReplHarness
from src.trainer import train_from_url

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def cmd_stats(args: argparse.Namespace) -> int:
    catalog = SongCatalogStore(args.catalog)
    print(catalog.format_stats_report())
    if args.inference:
        model = SongwritingReferenceModel(args.inference)
        print(model.format_report())
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    if getattr(args, "url", None):
        train_from_url(
            args.url,
            catalog_path=args.catalog,
            inference_path=args.inference,
        )
        return 0
    catalog = SongCatalogStore(args.catalog)
    model = SongwritingReferenceModel(args.inference)
    n = model.train_from_catalog(catalog)
    model.save()
    print(f"Trained inference model on {n} songs -> {args.inference}")
    print(model.format_report())
    return 0


def cmd_v6(args: argparse.Namespace) -> int:
    """Generate Suno V6 Studio JSON payload using Scansion-LM and Reference Model."""
    from src.llm import generate_suno_v6_payload
    from src.song_creator import create_complete_song_bundle

    resolved_theme = (getattr(args, "pos_theme", "") or getattr(args, "theme", "") or "dark glam electropop, cold radio pop, cinematic dance-pop").strip()
    resolved_title = (getattr(args, "title", "") or "New Name on the Door").strip()
    mode = getattr(args, "mode", "3k")

    if getattr(args, "assets", False) or mode == "both":
        bundle = create_complete_song_bundle(
            title=resolved_title,
            theme=resolved_theme,
            vocal_gender=args.vocal,
            bpm=args.bpm,
            out_dir="output/songs",
        )
        print("\n--- 3K SUNO STUDIO V6 JSON PAYLOAD ---\n")
        print(json.dumps(bundle["payload_3k"], indent=2, ensure_ascii=False))
        print(f"\n[+] 3K JSON Length: {bundle['len_3k']:,} characters")
        print("\n--- 5K EXTENDED STUDIO V6 JSON PAYLOAD ---\n")
        print(json.dumps(bundle["payload_5k"], indent=2, ensure_ascii=False))
        print(f"\n[+] 5K JSON Length: {bundle['len_5k']:,} characters")
        return 0

    payload = generate_suno_v6_payload(
        theme=resolved_theme,
        title=resolved_title,
        tier=args.tier,
        vocal_gender=args.vocal,
        bpm=args.bpm,
        style_weight=args.style_weight,
        weirdness_constraint=args.weirdness_constraint,
        audio_weight=args.audio_weight,
        model_version=args.model_version,
        engine=args.engine,
        mode=mode,
    )
    formatted = json.dumps(payload, indent=2, ensure_ascii=False)
    print(formatted)
    print(f"\n[+] Suno Studio {mode.upper()} JSON Length: {len(formatted):,} characters", file=sys.stderr)
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(formatted, encoding="utf-8")
        print(f"[+] Saved Suno V6 JSON payload -> {p}", file=sys.stderr)
    return 0


def cmd_song(args: argparse.Namespace) -> int:
    """Generate complete new song with 3k & 5k JSON payloads, synchronized LRC lyrics, production brief, and cover prompt."""
    from src.song_creator import create_complete_song_bundle

    resolved_theme = (getattr(args, "pos_theme", "") or getattr(args, "theme", "") or "dark glam electropop, cold radio pop, cinematic dance-pop").strip()
    resolved_title = (getattr(args, "title", "") or "").strip()
    vocal = getattr(args, "vocal", "")
    bpm = getattr(args, "bpm", 122)
    artist = getattr(args, "artist", "SUNO STUDIO MASTER")
    custom_text = getattr(args, "text", "")
    ref_url = getattr(args, "ref", "")
    image_prompt = getattr(args, "image_prompt", "")
    render_video = not getattr(args, "no_video", False)
    out_dir = getattr(args, "out_dir", "output/songs")
    lyrics = getattr(args, "lyrics", "")
    lyrics_file = getattr(args, "lyrics_file", None)
    lipogram = getattr(args, "lipogram", "")
    engine = getattr(args, "engine", "llm")

    bundle = create_complete_song_bundle(
        title=resolved_title,
        theme=resolved_theme,
        vocal_gender=vocal,
        bpm=bpm,
        artist=artist,
        custom_text=custom_text,
        reference_image_url=ref_url,
        image_prompt=image_prompt,
        render_video=render_video,
        out_dir=out_dir,
        lyrics=lyrics,
        lyrics_file=lyrics_file,
        lipogram=lipogram,
        engine=engine,
    )
    print("\n--- 3K SUNO STUDIO V6 JSON PAYLOAD ---\n")
    print(json.dumps(bundle["payload_3k"], indent=2, ensure_ascii=False))
    print(f"\n[+] 3K JSON Length: {bundle['len_3k']:,} characters")
    print("\n--- 5K EXTENDED STUDIO V6 JSON PAYLOAD ---\n")
    print(json.dumps(bundle["payload_5k"], indent=2, ensure_ascii=False))
    print(f"\n[+] 5K JSON Length: {bundle['len_5k']:,} characters")
    if bundle.get("cover_png"):
        print(f"\n[+] Album Cover (PNG): {bundle['cover_png']}")
    if bundle.get("teaser_video"):
        print(f"[+] 10s Video Teaser:  {bundle['teaser_video']} (1080p Ultra HD 60fps MP4)")
    return 0


def cmd_wizard(args: argparse.Namespace) -> int:
    """Launch the interactive guided hit song creation wizard."""
    from src.wizard import run_guided_wizard
    out_dir = getattr(args, "out_dir", "output/songs")
    run_guided_wizard(out_dir=out_dir, engine=getattr(args, "engine", "llm"))
    return 0


def cmd_payload_suite(args: argparse.Namespace) -> int:
    """Generate complete library of 3k and 5k JSON payloads."""
    from src.payload_suite import generate_all_payload_suites

    res = generate_all_payload_suites(
        out_dir_3k=args.out_3k,
        out_dir_5k=args.out_5k,
    )
    print(f"[+] Completed payload suite generation: {res['count']} archetypes generated in both 3k and 5k specifications.")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Train (optional), then write one or more Suno prompt files from the model."""
    engine = getattr(args, "engine", "llm")
    if engine in ("llm", "hybrid"):
        from src.llm import generate_suno_v6_payload

    catalog = SongCatalogStore(args.catalog)
    model = SongwritingReferenceModel(args.inference)
    if args.retrain or not model._state.get("trained_at"):
        n = model.train_from_catalog(catalog)
        model.save()
        print(f"Trained on {n} songs (lyrics={model._state.get('songs_with_lyrics')})")
    themes = [t.strip() for t in (args.themes or args.theme or "viral night drive").split(",") if t.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, theme in enumerate(themes[: max(1, args.count)]):
        stamp = f"{i+1:02d}"
        slug = re.sub(r'[^a-z0-9]+', '_', theme.lower())[:40].strip('_')
        path = out_dir / f"model_gen_{stamp}_{slug}.txt"

        if engine in ("llm", "hybrid"):
            v6_payload = generate_suno_v6_payload(
                theme=theme,
                title=args.title or theme.title(),
                tier=args.tier,
                vocal_gender=getattr(args, "vocal", "f"),
                engine=engine,
            )
            paste_ready = (
                f"TITLE\n{v6_payload['title']}\n\n"
                f"STYLE\n{v6_payload['style']}\n\n"
                f"EXCLUDE\n{v6_payload['negativeTags']}\n\n"
                f"LYRICS\n{v6_payload['prompt']}\n"
            )
            path.write_text(paste_ready, encoding="utf-8")
            json_path = path.with_suffix(".json")
            json_path.write_text(json.dumps(v6_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            written.append(path)
            print(f"Wrote {json_path}")
        else:
            written.append(model.write_prompt_file(path, theme=theme, tier=args.tier, title=args.title or ""))
            seed = model.generate_prompt_seed(theme=theme, tier=args.tier, title=args.title or "")
            json_path = path.with_suffix(".json")
            json_path.write_text(json.dumps(seed, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Wrote {json_path}")
    print(model.format_report())
    for p in written:
        print(f"Wrote {p}")
    return 0


def cmd_suggest(args: argparse.Namespace) -> int:
    catalog = SongCatalogStore(args.catalog)
    model = SongwritingReferenceModel(args.inference)
    if not model._state.get("trained_at"):
        model.train_from_catalog(catalog)
        model.save()
    seed = model.generate_prompt_seed(theme=args.theme, tier=args.tier, title=args.title or "")
    print(json.dumps({k: v for k, v in seed.items() if k != "paste_ready"}, indent=2, ensure_ascii=False))
    if args.write:
        path = Path(args.write)
        model.write_prompt_file(path, theme=args.theme, tier=args.tier, title=args.title or "")
        print(f"\nWrote paste-ready prompt -> {path}")
    else:
        print("\n--- PASTE READY ---\n")
        print(seed.get("paste_ready") or "")
    if args.unused:
        unused = model.suggest_unused_style_pack(catalog)
        print("\nUnused / novel style pack:")
        print(unused.style_pack)
    return 0


def cmd_similar(args: argparse.Namespace) -> int:
    catalog = SongCatalogStore(args.catalog)
    model = SongwritingReferenceModel(args.inference)
    rec = catalog.get(args.song_id)
    if rec is None:
        print(f"Song not in catalog: {args.song_id}", file=sys.stderr)
        return 1
    similar = model.discover_similar(rec, catalog, limit=args.limit)
    for s in similar:
        print(f"{s.score:.3f} | {s.like_count} likes | {s.title[:60]} | {s.url}")
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    catalog = SongCatalogStore(args.catalog)
    n = catalog.reprocess_all()
    print(f"Reprocessed {n} songs in {args.catalog}")
    print(catalog.format_stats_report())
    return 0


def cmd_export_jsonl(args: argparse.Namespace) -> int:
    catalog = SongCatalogStore(args.catalog)
    n = catalog.export_jsonl(args.output, min_likes=args.min_likes)
    print(f"Exported {n} songs to {args.output}")
    return 0


def cmd_export_csv(args: argparse.Namespace) -> int:
    catalog = SongCatalogStore(args.catalog)
    fields = [
        "song_id", "url", "title", "prompt", "lyrics", "style_of_music",
        "tags", "genres", "styles", "artist_id", "external_like_count",
        "derived_traction_tier", "derived_style_signature", "lyric_line_count",
        "lyric_word_count", "structure_tags", "discovered_via", "first_seen_at",
    ]
    records = catalog.all_records()
    if args.min_likes:
        records = [r for r in records if r.external_like_count >= args.min_likes]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = rec.to_dict()
            for list_key in ("tags", "genres", "styles", "structure_tags"):
                row[list_key] = "|".join(row.get(list_key) or [])
            writer.writerow(row)
    print(f"Exported {len(records)} songs to {args.output}")
    return 0


def cmd_repl(args: argparse.Namespace) -> int:
    cat = Path(args.catalog)
    inf = Path(args.inference)
    if not cat.exists() and Path("models/suno_song_catalog.json").exists():
        cat = Path("models/suno_song_catalog.json")
    if not inf.exists() and Path("models/suno_song_inference_model.json").exists():
        inf = Path("models/suno_song_inference_model.json")
    harness = SunoReplHarness(catalog_path=cat, inference_path=inf)
    harness.cmdloop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Suno song dataset & inference tools")
    p.add_argument("--catalog", default="models/suno_song_catalog.json", help="Song catalog JSON path")
    p.add_argument("--inference", default="models/suno_song_inference_model.json", help="Inference model JSON path")
    sub = p.add_subparsers(dest="command")

    stats = sub.add_parser("stats", help="Print catalog and model stats")
    stats.set_defaults(func=cmd_stats)

    train = sub.add_parser("train", help="Train/retrain inference model from catalog or URL")
    train.add_argument("url", nargs="?", default="", help="Optional Suno URL to ingest and retrain")
    train.set_defaults(func=cmd_train)

    gen = sub.add_parser("generate", help="Write Suno prompt file(s) from the inference model or LLM")
    gen.add_argument("--theme", default="viral night drive", help="Theme (or comma-separated with --themes)")
    gen.add_argument("--themes", default="", help="Comma-separated themes")
    gen.add_argument("--title", default="", help="Optional title override")
    gen.add_argument("--tier", default="high", choices=("low", "medium", "high", "viral"))
    gen.add_argument("--count", type=int, default=1)
    gen.add_argument("--engine", default="llm", choices=("llm", "hybrid", "reference"), help="Inference engine (llm, hybrid, reference)")
    gen.add_argument("--vocal", default="f", choices=("f", "m"), help="Vocal gender for LLM/hybrid mode")
    gen.add_argument("--out-dir", default="output/prompts")
    gen.add_argument("--retrain", action="store_true", help="Retrain model from catalog first")
    gen.set_defaults(func=cmd_generate)

    v6 = sub.add_parser("v6", help="Generate full Suno V6 Studio JSON payload matching target specification")
    v6.add_argument("pos_theme", nargs="?", default="", help="Optional positional theme")
    v6.add_argument("--theme", default="", help="Theme/Genre style")
    v6.add_argument("--title", default="", help="Song Title")
    v6.add_argument("--tier", default="high", choices=("low", "medium", "high", "viral"))
    v6.add_argument("--gender", "--vocal", dest="vocal", default="f", choices=("f", "m"), help="Vocal gender (f or m)")
    v6.add_argument("--bpm", type=int, default=122, help="BPM")
    v6.add_argument("--style-weight", type=float, default=0.84, help="Style weight slider value")
    v6.add_argument("--weirdness-constraint", type=float, default=0.34, help="Weirdness constraint slider value")
    v6.add_argument("--audio-weight", type=float, default=0.0, help="Audio weight slider value")
    v6.add_argument("--model-version", default="V6", help="Target Suno model version (V6, V5.5, V4)")
    v6.add_argument("--engine", default="llm", choices=("llm", "hybrid", "reference"), help="Generation engine")
    v6.add_argument("--mode", default="3k", choices=("3k", "5k", "both"), help="Payload length mode (3k, 5k, or both)")
    v6.add_argument("--assets", action="store_true", help="Generate complete asset bundle (prompts, LRC, brief, cover art)")
    v6.add_argument("-o", "--out", default="", help="Optional output JSON filepath")
    v6.set_defaults(func=cmd_v6)

    song = sub.add_parser("song", help="Generate a COMPLETE new song with 3k & 5k JSON payloads, LRC, brief, and cover art")
    song.add_argument("pos_theme", nargs="?", default="", help="Optional theme/genre/prompt")
    song.add_argument("--theme", default="", help="Theme or genre style")
    song.add_argument("--title", default="", help="Song title")
    song.add_argument("--artist", default="SUNO STUDIO MASTER", help="Artist name")
    song.add_argument("--gender", "--vocal", dest="vocal", default="", choices=("", "f", "m"), help="Vocal gender (f or m, defaults to auto-detect)")
    song.add_argument("--bpm", type=int, default=122, help="BPM")
    song.add_argument("--text", default="", help="Custom text overlay to render on cover art")
    song.add_argument("--ref", default="", help="Base reference image URL (HTTP/HTTPS) for cover art")
    song.add_argument("--image-prompt", default="", help="Visual image prompt for AI cover art")
    song.add_argument("--no-video", action="store_true", help="Skip generating the 10-second teaser video")
    song.add_argument("--out-dir", default="output/songs", help="Output directory for song bundle")
    song.add_argument("--lyrics", "-l", default="", help="Custom lyrics (optional)")
    song.add_argument("--lyrics-file", "-lf", default="", help="Path to custom lyrics file (optional)")
    song.add_argument("--lipogram", default="", help="Lipogram constraint letter (e.g. 'e')")
    song.add_argument("--engine", default="llm", choices=("llm", "hybrid", "reference", "dynamic"), help="Inference engine")
    song.set_defaults(func=cmd_song)

    wiz = sub.add_parser("wizard", help="Interactive step-by-step Hit Song Creation Wizard")
    wiz.add_argument("--out-dir", default="output/songs", help="Output directory for generated song bundle")
    wiz.set_defaults(func=cmd_wizard)

    psuite = sub.add_parser("payload-suite", help="Generate complete library of 3k and 5k JSON payloads across 7k song archetypes")
    psuite.add_argument("--out-3k", default="output/payloads_3k", help="Directory for 3k payloads")
    psuite.add_argument("--out-5k", default="output/payloads_5k", help="Directory for 5k payloads")
    psuite.set_defaults(func=cmd_payload_suite)

    sug = sub.add_parser("suggest", help="Generate style/structure prompt seed from learned data")
    sug.add_argument("--theme", default="", help="Optional theme words")
    sug.add_argument("--title", default="", help="Optional song title")
    sug.add_argument("--tier", default="high", choices=("low", "medium", "high", "viral"))
    sug.add_argument("--unused", action="store_true", help="Also print unused style pack")
    sug.add_argument("--write", default="", help="Write paste-ready prompt to this path")
    sug.set_defaults(func=cmd_suggest)

    sim = sub.add_parser("similar", help="Find similar songs in catalog")
    sim.add_argument("song_id", help="Song UUID")
    sim.add_argument("--limit", type=int, default=8)
    sim.set_defaults(func=cmd_similar)

    reb = sub.add_parser("rebuild", help="Recompute derived features for the full catalog")
    reb.set_defaults(func=cmd_rebuild)

    exj = sub.add_parser("export-jsonl", help="Export catalog to JSONL for ML training")
    exj.add_argument("-o", "--output", default="output/songs.jsonl")
    exj.add_argument("--min-likes", type=int, default=0)
    exj.set_defaults(func=cmd_export_jsonl)

    exc = sub.add_parser("export-csv", help="Export catalog to CSV")
    exc.add_argument("-o", "--output", default="output/songs.csv")
    exc.add_argument("--min-likes", type=int, default=0)
    exc.set_defaults(func=cmd_export_csv)

    repl = sub.add_parser("repl", help="Start interactive REPL terminal harness")
    repl.set_defaults(func=cmd_repl)

    return p


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        # Default with no arguments: start interactive REPL!
        return cmd_repl(argparse.Namespace(
            catalog="models/suno_song_catalog.json",
            inference="models/suno_song_inference_model.json"
        ))
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
