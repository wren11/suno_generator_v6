"""Ingest Suno song URLs, download audio, transcribe lyrics, and retrain inference model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.catalog import SongCatalogStore
from src.downloader import SunoSongDownloader
from src.inference import SongwritingReferenceModel
from src.transcriber import SunoAudioTranscriber

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def sync_to_scansion_extracts(title: str, lyrics: str, style: str = "") -> None:
    """Sync newly ingested hit songs directly into Scansion-LM and corpus JSONL files so causal LM learns them."""
    if not lyrics or len(lyrics.splitlines()) < 4:
        return
    try:
        from src.scansion_lm.paths import USER_EXTRACTS
        row = {
            "title": title,
            "idea": style or "Hit track scansion",
            "text": lyrics,
            "sung": [ln.strip() for ln in lyrics.splitlines() if ln.strip() and not ln.strip().startswith("[")][:8],
        }
        line_bytes = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
        USER_EXTRACTS.parent.mkdir(parents=True, exist_ok=True)
        with USER_EXTRACTS.open("ab") as f:
            f.write(line_bytes)
        
        # Also mirror to dist foundry data if present
        dist_extracts = Path(__file__).resolve().parent.parent / "dist" / "foundry" / "data" / "user_extracts.jsonl"
        if dist_extracts.parent.exists() and dist_extracts.resolve() != USER_EXTRACTS.resolve():
            with dist_extracts.open("ab") as f:
                f.write(line_bytes)

        # Incrementally append to massive training corpus
        try:
            from src.corpus_builder import append_song_to_corpus
            append_song_to_corpus(title=title, lyrics=lyrics, style=style)
        except Exception:
            pass
    except Exception:
        pass


def train_from_url(
    song_url_or_id: str,
    *,
    catalog_path: str | Path = "models/suno_song_catalog.json",
    inference_path: str | Path = "models/suno_song_inference_model.json",
    audio_dir: str | Path = "output/audio",
    transcripts_dir: str | Path = "output/transcripts",
    hf_token: str | None = None,
    whisper_model: str = "base",
) -> dict:
    catalog_path = Path(catalog_path)
    inference_path = Path(inference_path)

    print("=" * 60)
    print("  SUNO SONG TRAINER PIPELINE")
    print("=" * 60)
    print(f"Target Song URL / ID: {song_url_or_id}")
    print(f"Catalog DB:           {catalog_path}")
    print(f"Inference Model:      {inference_path}")
    print("-" * 60)

    # Step 1: Download audio and scrape metadata
    downloader = SunoSongDownloader(output_dir=audio_dir)
    song_data = downloader.fetch_song(song_url_or_id, download_audio=True)

    print(f"\n[+] Ingested Track Metadata:")
    print(f"    Title:    {song_data.title}")
    print(f"    Artist:   {song_data.artist_name} (@{song_data.artist_id})")
    print(f"    Style:    {song_data.style_of_music}")
    print(f"    Traction: {song_data.like_count} likes, {song_data.play_count} plays")
    if song_data.downloaded_audio_path:
        print(f"    Audio:    {song_data.downloaded_audio_path}")

    # Step 2: Listen to audio & transcribe lyrics
    transcriber = SunoAudioTranscriber(transcripts_dir=transcripts_dir)
    lyrics = ""
    if song_data.downloaded_audio_path and song_data.downloaded_audio_path.exists():
        print("\n[*] Listening to audio stream and transcribing lyrics...")
        t_res = transcriber.transcribe(
            song_data.downloaded_audio_path,
            song_id=song_data.song_id,
            hf_token=hf_token,
            model_size=whisper_model,
            existing_prompt_lyrics=song_data.lyrics or song_data.prompt,
        )
        lyrics = t_res["lyrics"]
    else:
        print("[!] No audio file downloaded; using embedded prompt lyrics if present.")
        lyrics = song_data.lyrics or song_data.prompt

    print("\n--- TRANSCRIBED SONG LYRICS ---")
    print(lyrics[:600] + ("..." if len(lyrics) > 600 else ""))
    print("--------------------------------\n")

    # Step 3: Ingest into catalog
    catalog = SongCatalogStore(catalog_path)
    payload = {
        "song_id": song_data.song_id,
        "url": song_data.url,
        "title": song_data.title,
        "prompt": song_data.prompt,
        "lyrics": lyrics,
        "style_of_music": song_data.style_of_music,
        "tags": song_data.tags,
        "artist_id": song_data.artist_id,
        "artist_name": song_data.artist_name,
        "audio_url": song_data.audio_url,
        "video_url": song_data.video_url,
        "external_like_count": song_data.like_count,
        "play_count": song_data.play_count,
        "duration_seconds": song_data.duration_seconds,
        "discovered_via": "trainer_pipeline",
        "raw_feed_snapshot": song_data.raw_metadata,
    }
    rec = catalog.ingest(payload, discovered_via="trainer_url")
    catalog.save()
    if lyrics:
        sync_to_scansion_extracts(song_data.title, lyrics, song_data.style_of_music)
    print(f"[+] Updated catalog: {len(catalog.all_records())} songs stored -> {catalog_path}")

    # Step 4: Retrain inference model
    print("[*] Retraining SongwritingReferenceModel...")
    model = SongwritingReferenceModel(inference_path)
    trained_count = model.train_from_catalog(catalog)
    model.save()
    print(f"[+] Retrained model on {trained_count} catalog songs -> {inference_path}")

    # Also update root models if present
    root_model = Path("models/suno_song_inference_model.json")
    if root_model.parent.exists() and root_model != inference_path:
        model.model_path = root_model
        model.save()
        model.model_path = inference_path

    print("\n" + model.format_report())
    return {
        "song_id": song_data.song_id,
        "title": song_data.title,
        "lyrics": lyrics,
        "catalog_count": trained_count,
        "model_path": str(inference_path),
    }


def parse_prompt_text_file(text: str) -> dict[str, str]:
    """Extract TITLE, STYLE, EXCLUDE, and LYRICS from Suno prompt text files."""
    import re
    out = {"title": "", "style": "", "exclude": "", "lyrics": ""}
    cur_key = ""
    buf: list[str] = []

    def flush():
        if cur_key:
            val = "\n".join(buf).strip()
            cleaned_lines = [l for l in val.splitlines() if not re.match(r"^[=\-_]{4,}$", l.strip())]
            out[cur_key] = "\n".join(cleaned_lines).strip()
        buf.clear()

    for line in text.splitlines():
        upper = line.strip().upper()
        if re.match(r"^[=\-_]{4,}$", upper):
            continue
        if upper.startswith("TITLE") and len(upper) < 20:
            flush()
            cur_key = "title"
        elif (upper.startswith("STYLE") or "STYLE (" in upper) and len(upper) < 35:
            flush()
            cur_key = "style"
        elif (upper.startswith("EXCLUDE") or "EXCLUDE (" in upper) and len(upper) < 35:
            flush()
            cur_key = "exclude"
        elif (upper.startswith("LYRICS") or "LYRICS (" in upper or "HOOK" in upper) and len(upper) < 65:
            flush()
            cur_key = "lyrics"
        else:
            if cur_key:
                buf.append(line)
    flush()
    return out


def train_from_profile(
    handle: str = "wren",
    *,
    catalog_path: str | Path = "models/suno_song_catalog.json",
    inference_path: str | Path = "models/suno_song_inference_model.json",
    max_pages: int = 50,
) -> dict:
    """Fetch all public songs from a Suno user profile (e.g. suno.com/@wren) and retrain."""
    import re
    clean_handle = handle.strip().lstrip("@")
    if "/" in clean_handle:
        clean_handle = clean_handle.split("/")[-1].lstrip("@")

    catalog_path = Path(catalog_path)
    inference_path = Path(inference_path)

    print("=" * 60)
    print(f"  SUNO PROFILE INGESTION & TRAINING: @{clean_handle}")
    print("=" * 60)
    print(f"Catalog DB:      {catalog_path}")
    print(f"Inference Model: {inference_path}")
    print("-" * 60)

    downloader = SunoSongDownloader()
    clips = downloader.fetch_profile_clips(clean_handle, max_pages=max_pages)
    if not clips:
        print(f"[!] No clips found for profile @{clean_handle}")
        return {"handle": clean_handle, "ingested": 0}

    catalog = SongCatalogStore(catalog_path)
    ingested = 0

    print(f"[*] Ingesting {len(clips)} tracks from @{clean_handle} into catalog...")
    for c in clips:
        cid = str(c.get("id") or "").strip().lower()
        if not cid:
            continue
        meta = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
        title = str(c.get("title") or "WREN Track").strip()
        tags_raw = str(meta.get("tags") or c.get("tags") or "")
        tags = [t.strip() for t in re.split(r"[,;/|]+", tags_raw) if t.strip()]

        lyrics = str(meta.get("prompt") or c.get("lyrics") or "").strip()
        style = tags_raw

        payload = {
            "song_id": cid,
            "url": f"https://suno.com/song/{cid}",
            "title": title,
            "prompt": style,
            "lyrics": lyrics,
            "style_of_music": style,
            "tags": tags,
            "artist_id": clean_handle,
            "artist_name": str(c.get("display_name") or clean_handle.upper()),
            "audio_url": str(c.get("video_url") or f"https://cdn1.suno.ai/{cid}.mp4"),
            "video_url": str(c.get("video_url") or f"https://cdn1.suno.ai/{cid}.mp4"),
            "external_like_count": int(c.get("upvote_count") or c.get("like_count") or 0),
            "play_count": int(c.get("play_count") or 0),
            "duration_seconds": float(meta.get("duration") or 0.0) if meta.get("duration") else None,
            "discovered_via": f"profile_{clean_handle}",
            "raw_feed_snapshot": c,
        }
        catalog.ingest(payload, discovered_via=f"profile_{clean_handle}")
        ingested += 1
        if lyrics:
            sync_to_scansion_extracts(title, lyrics, style)

    catalog.save()
    print(f"[+] Successfully ingested {ingested} tracks into {catalog_path}")

    # Retrain inference model
    print("[*] Retraining SongwritingReferenceModel...")
    model = SongwritingReferenceModel(inference_path)
    trained_count = model.train_from_catalog(catalog)
    model.save()
    print(f"[+] Retrained model on {trained_count} catalog songs -> {inference_path}")

    root_model = Path("models/suno_song_inference_model.json")
    if root_model.parent.exists() and root_model != inference_path:
        model.model_path = root_model
        model.save()

    print("\n" + model.format_report())
    return {
        "handle": clean_handle,
        "ingested": ingested,
        "catalog_count": trained_count,
        "model_path": str(inference_path),
    }


def train_from_trending(
    feed_ids: tuple[str, ...] = ("trending", "new_songs"),
    *,
    catalog_path: str | Path = "models/suno_song_catalog.json",
    inference_path: str | Path = "models/suno_song_inference_model.json",
    max_items_per_feed: int = 50,
) -> dict:
    """Fetch live trending songs from Suno explore API, ingest into catalog, and retrain reference model."""
    import re
    catalog_path = Path(catalog_path)
    inference_path = Path(inference_path)

    print("=" * 60)
    print("  SUNO LIVE TRENDING & EXPLORE FEED INGESTION & TRAINING")
    print("=" * 60)
    print(f"Feed IDs:        {', '.join(feed_ids)}")
    print(f"Catalog DB:      {catalog_path}")
    print(f"Inference Model: {inference_path}")
    print("-" * 60)

    downloader = SunoSongDownloader()
    catalog = SongCatalogStore(catalog_path)
    total_ingested = 0

    for fid in feed_ids:
        print(f"[*] Fetching Suno unified feed: '{fid}' ...")
        clips = downloader.fetch_unified_feed(feed_id=fid, page_size=50, max_items=max_items_per_feed)
        for c in clips:
            cid = str(c.get("id") or "").strip().lower()
            if not cid:
                continue
            meta = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
            title = str(c.get("title") or "Suno Trending Hit").strip()
            tags_raw = str(meta.get("tags") or c.get("tags") or "")
            tags = [t.strip() for t in re.split(r"[,;/|]+", tags_raw) if t.strip()]
            lyrics = str(meta.get("prompt") or c.get("lyrics") or "").strip()
            style = tags_raw
            handle = str(c.get("handle") or "suno_community")

            payload = {
                "song_id": cid,
                "url": f"https://suno.com/song/{cid}",
                "title": title,
                "prompt": style,
                "lyrics": lyrics,
                "style_of_music": style,
                "tags": tags,
                "artist_id": handle,
                "artist_name": str(c.get("display_name") or handle.upper()),
                "audio_url": str(c.get("video_url") or c.get("audio_url") or f"https://cdn1.suno.ai/{cid}.mp4"),
                "video_url": str(c.get("video_url") or f"https://cdn1.suno.ai/{cid}.mp4"),
                "external_like_count": int(c.get("upvote_count") or c.get("like_count") or 0),
                "play_count": int(c.get("play_count") or 0),
                "duration_seconds": float(meta.get("duration") or 0.0) if meta.get("duration") else None,
                "discovered_via": f"unified_feed_{fid}",
                "raw_feed_snapshot": c,
            }
            catalog.ingest(payload, discovered_via=f"unified_feed_{fid}")
            total_ingested += 1
            if lyrics:
                sync_to_scansion_extracts(title, lyrics, style)

    catalog.save()
    print(f"[+] Total live trending songs ingested/updated: {total_ingested}")

    # Sync to dist catalog if exists
    dist_cat = Path("dist/models/suno_song_catalog.json")
    if dist_cat.exists() and dist_cat.resolve() != catalog_path.resolve():
        try:
            import shutil
            shutil.copy2(catalog_path, dist_cat)
        except Exception:
            pass

    # Retrain inference model
    print("[*] Retraining SongwritingReferenceModel...")
    model = SongwritingReferenceModel(inference_path)
    trained_count = model.train_from_catalog(catalog)
    model.save()
    print(f"[+] Retrained model on {trained_count} catalog songs -> {inference_path}")

    # Sync to dist inference model
    dist_inf = Path("dist/models/suno_song_inference_model.json")
    if dist_inf.exists() and dist_inf.resolve() != inference_path.resolve():
        try:
            import shutil
            shutil.copy2(inference_path, dist_inf)
        except Exception:
            pass

    print("\n" + model.format_report())
    return {
        "ingested": total_ingested,
        "catalog_count": trained_count,
        "model_path": str(inference_path),
    }


def train_from_created(
    *,
    catalog_path: str | Path = "models/suno_song_catalog.json",
    inference_path: str | Path = "models/suno_song_inference_model.json",
    created_catalog_path: str | Path = "E:/work/suno/CREATED_CATALOG.json",
    prompts_dir: str | Path = "E:/work/suno/suno_prompts",
    local_prompts_dir: str | Path = "output/prompts",
) -> dict:
    """Ingest handcrafted and created songs from CREATED_CATALOG.json and prompt output files."""
    import re
    import json
    catalog_path = Path(catalog_path)
    inference_path = Path(inference_path)
    created_catalog_path = Path(created_catalog_path)
    prompts_dir = Path(prompts_dir)
    local_prompts_dir = Path(local_prompts_dir)

    print("=" * 60)
    print("  SUNO CREATED SONGS INGESTION & RETRAINING")
    print("=" * 60)
    print(f"Created Catalog: {created_catalog_path}")
    print(f"Prompts Dir:     {prompts_dir}")
    print(f"Catalog DB:      {catalog_path}")
    print("-" * 60)

    catalog = SongCatalogStore(catalog_path)
    ingested = 0

    # 1. Ingest from CREATED_CATALOG.json
    if created_catalog_path.exists():
        try:
            cat_data = json.loads(created_catalog_path.read_text(encoding="utf-8"))
            songs = cat_data.get("songs") or []
            print(f"[*] Found {len(songs)} created song entries in {created_catalog_path.name}")
            for item in songs:
                title = str(item.get("title") or "Handcrafted Track").strip()
                source_file = item.get("source") or ""
                style = ""
                lyrics = ""
                exclude = ""

                # Try reading source prompt file
                if source_file and (prompts_dir / source_file).exists():
                    p_text = (prompts_dir / source_file).read_text(encoding="utf-8", errors="replace")
                    parsed = parse_prompt_text_file(p_text)
                    style = parsed.get("style") or ""
                    lyrics = parsed.get("lyrics") or ""
                    exclude = parsed.get("exclude") or ""
                    if parsed.get("title"):
                        title = parsed.get("title")

                urls = item.get("urls") or []
                if not urls and item.get("url_1"):
                    urls.append(item.get("url_1"))
                if not urls and item.get("url"):
                    urls.append(item.get("url"))

                for u in urls:
                    from src.catalog import song_id_from_url
                    sid = song_id_from_url(u)
                    if not sid:
                        continue
                    tags = [t.strip() for t in re.split(r"[,;/|]+", style) if t.strip()]
                    payload = {
                        "song_id": sid,
                        "url": u,
                        "title": title,
                        "prompt": style,
                        "lyrics": lyrics,
                        "style_of_music": style,
                        "negative_prompt": exclude,
                        "tags": tags,
                        "artist_id": "wren",
                        "artist_name": "WREN",
                        "audio_url": f"https://cdn1.suno.ai/{sid}.mp4",
                        "video_url": f"https://cdn1.suno.ai/{sid}.mp4",
                        "discovered_via": "created_catalog",
                    }
                    catalog.ingest(payload, discovered_via="created_catalog")
                    ingested += 1
                    if lyrics:
                        sync_to_scansion_extracts(title, lyrics, style)
        except Exception as e:
            print(f"[!] Error processing {created_catalog_path}: {e}")

    # 2. Ingest any generated prompts from local output/prompts/
    if local_prompts_dir.exists():
        for jf in local_prompts_dir.glob("*.json"):
            try:
                p_data = json.loads(jf.read_text(encoding="utf-8"))
                p_title = p_data.get("title") or jf.stem
                p_style = p_data.get("style") or p_data.get("style_of_music") or ""
                p_lyrics = p_data.get("prompt") or p_data.get("lyrics") or ""
                p_exclude = p_data.get("negativeTags") or p_data.get("exclude") or ""
                if p_lyrics or p_style:
                    import hashlib
                    gen_id = hashlib.md5(f"{p_title}_{p_lyrics[:50]}".encode()).hexdigest()
                    gen_uuid = f"{gen_id[:8]}-{gen_id[8:12]}-{gen_id[12:16]}-{gen_id[16:20]}-{gen_id[20:32]}"
                    tags = [t.strip() for t in re.split(r"[,;/|]+", p_style) if t.strip()]
                    payload = {
                        "song_id": gen_uuid,
                        "url": f"https://suno.com/song/{gen_uuid}",
                        "title": p_title,
                        "prompt": p_style,
                        "lyrics": p_lyrics,
                        "style_of_music": p_style,
                        "negative_prompt": p_exclude,
                        "tags": tags,
                        "artist_id": "wren",
                        "artist_name": "WREN",
                        "discovered_via": "generated_prompts",
                    }
                    catalog.ingest(payload, discovered_via="generated_prompts")
                    ingested += 1
                    if p_lyrics:
                        sync_to_scansion_extracts(p_title, p_lyrics, p_style)
            except Exception:
                pass

    catalog.save()
    print(f"[+] Total created song records ingested/updated: {ingested}")

    # Retrain inference model
    print("[*] Retraining SongwritingReferenceModel...")
    model = SongwritingReferenceModel(inference_path)
    trained_count = model.train_from_catalog(catalog)
    model.save()
    print(f"[+] Retrained model on {trained_count} catalog songs -> {inference_path}")

    root_model = Path("models/suno_song_inference_model.json")
    if root_model.parent.exists() and root_model != inference_path:
        model.model_path = root_model
        model.save()

    print("\n" + model.format_report())
    return {
        "ingested": ingested,
        "catalog_count": trained_count,
        "model_path": str(inference_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Suno song URL, download audio, transcribe, and retrain.")
    parser.add_argument("target", nargs="?", default="", help="Suno song URL, profile (@wren), 'trending', or 'created'")
    parser.add_argument("--catalog", default="models/suno_song_catalog.json", help="Path to catalog JSON")
    parser.add_argument("--inference", default="models/suno_song_inference_model.json", help="Path to inference model JSON")
    parser.add_argument("--audio-dir", default="output/audio", help="Directory to save downloaded audio")
    parser.add_argument("--transcripts-dir", default="output/transcripts", help="Directory to save transcripts")
    parser.add_argument("--profile", default="", help="Suno user profile handle (e.g. @wren)")
    parser.add_argument("--created", action="store_true", help="Train on created songs and prompts")
    parser.add_argument("--hf-token", default=None, help="Optional Hugging Face API token for free serverless Whisper")
    parser.add_argument("--whisper-model", default="base", help="Local whisper model size (tiny, base, small)")

    args = parser.parse_args()
    target = (args.target or "").strip()

    if args.created or target.lower() in ("created", "new", "--created"):
        train_from_created(catalog_path=args.catalog, inference_path=args.inference)
        return 0

    if not target or target.lower() in ("trending", "explore", "top", "--trending"):
        print("[*] Running Suno.com live trending ingestion & auto-training...")
        train_from_trending(catalog_path=args.catalog, inference_path=args.inference)
        return 0

    if args.profile or target.startswith("@") or "suno.com/@" in target or target.lower() == "wren":
        handle = args.profile or target
        train_from_profile(handle, catalog_path=args.catalog, inference_path=args.inference)
        return 0

    if target.lower() in ("all", "full"):
        train_from_trending(catalog_path=args.catalog, inference_path=args.inference)
        train_from_profile("wren", catalog_path=args.catalog, inference_path=args.inference)
        train_from_created(catalog_path=args.catalog, inference_path=args.inference)
        return 0

    train_from_url(
        target,
        catalog_path=args.catalog,
        inference_path=args.inference,
        audio_dir=args.audio_dir,
        transcripts_dir=args.transcripts_dir,
        hf_token=args.hf_token,
        whisper_model=args.whisper_model,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
